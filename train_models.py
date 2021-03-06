import os
from scipy import stats
from shutil import copyfile
import deepfake
from figures import profiles_viz
from CellData import CellData
import numpy as np
import pandas as pd
import random

random.seed(0)
np.random.seed(0)

# parameters
wdir = "results_2cells"
test_folds = ["1"]
# test_folds = range(1, 11)
# test_folds = ["antibiotics_ids", "adrenergic_ids", "cholinergic_ids",
#               "5-HT modulator_ids", "TKI_ids", "COX inh._ids",
#               "histaminergic_ids", "antipsychotic_ids", "GABAergic_ids", "dopaminergic_ids"]
input_size = 978
latent_dim = 128
data_folder = "/home/user/data/DeepFake/" + wdir


def test_loss(prediction, ground_truth):
    return np.sqrt(np.mean((prediction - ground_truth) ** 2))


os.chdir(data_folder)
# copyfile("/home/user/PycharmProjects/DeepFake/deepfake.py", "temp")
print(data_folder)
df = pd.read_csv("../LINCS/GSE70138_Broad_LINCS_pert_info.txt", sep="\t")
good = []
tsne_perts = []
tsne_input = []
tsne_latent = []
for r, test_fold in enumerate(test_folds):
    test_fold = str(test_fold)
    tr_size = 1280
    cell_data = CellData("../LINCS/lincs_phase_1_2.tsv", "../LINCS/folds/" + test_fold)
    autoencoder, cell_decoders = deepfake.get_best_autoencoder(input_size, latent_dim,
                                                               cell_data, test_fold, 2)
    encoder = autoencoder.get_layer("encoder")
    results = {}
    img_count = 0
    seen_perts = []
    print("Total test objects: " + str(len(cell_data.test_data)))
    all_results = []
    good_perts = []
    test_trt = "trt_cp"
    vectors = []
    input_profiles = []
    perts_order = []
    for i in range(len(cell_data.test_data)):
        if i % 100 == 0:
            print(str(i) + " - ", end="", flush=True)
        test_meta_object = cell_data.test_meta[i]
        if test_meta_object[2] != test_trt:
            continue
        if test_meta_object[0] not in ["MCF7", "PC3"]:
            continue
        closest, closest_profile, mean_profile, all_profiles = cell_data.get_profile(cell_data.test_data,
                                                                                     cell_data.meta_dictionary_pert_test[
                                                                                         test_meta_object[1]],
                                                                                     test_meta_object)
        if closest_profile is None:
            continue
        # if test_meta_object[1] in seen_perts:
        #     continue
        seen_perts.append(test_meta_object[1])
        test_profile = np.asarray([cell_data.test_data[i]])
        weights = cell_decoders[cell_data.test_meta[i][0]]
        autoencoder.get_layer("decoder").set_weights(weights)
        decoded1 = autoencoder.predict(closest_profile)

        results["count"] = results.get("count", 0) + 1
        results["Our performance is: "] = results.get("Our performance is: ", 0) + test_loss(decoded1, test_profile)

        results["Our correlation is: "] = results.get("Our correlation is: ", 0) + \
                                          stats.pearsonr(decoded1.flatten(), test_profile.flatten())[0]

        predictions = []
        for p in all_profiles:
            predictions.append(autoencoder.predict(np.asarray([p])))

        special_decoded = np.mean(np.asarray(predictions), axis=0, keepdims=True)

        results["Our multi-correlation is: "] = results.get("Our multi-correlation is: ", 0) + \
                                                stats.pearsonr(special_decoded.flatten(), test_profile.flatten())[0]

        results["Our multi-performance is: "] = results.get("Our multi-performance is: ", 0) + \
                                                test_loss(special_decoded, test_profile)

        decoded1 = autoencoder.predict(mean_profile)
        results["Our performance is (mean profile): "] = results.get("Our performance is (mean profile): ",
                                                                     0) + test_loss(decoded1, test_profile)

        results["Our correlation (mean profile): "] = results.get("Our correlation (mean profile): ", 0) + \
                                                      stats.pearsonr(decoded1.flatten(), test_profile.flatten())[0]

        results["Baseline correlation (mean profile): "] = results.get("Baseline correlation (mean profile): ", 0) + \
                                                           stats.pearsonr(mean_profile.flatten(),
                                                                          test_profile.flatten())[0]

        results["Baseline performance (mean profile): "] = results.get("Baseline performance (mean profile): ", 0) + \
                                                           test_loss(mean_profile, test_profile)

        all_results.append(str(stats.pearsonr(special_decoded.flatten(), test_profile.flatten())[0]) + ", " +
                           str(stats.pearsonr(mean_profile.flatten(), test_profile.flatten())[0]) + ", "
                           + test_meta_object[0] + ", " + test_meta_object[1] + ", " + str(len(all_profiles)))

        results["closest profile: "] = results.get("closest profile: ", 0) + test_loss(closest_profile, test_profile)
        results["closest profile correlation is: "] = results.get("closest profile correlation is: ", 0) + \
                                                      stats.pearsonr(closest_profile.flatten(), test_profile.flatten())[
                                                          0]
        bp = stats.pearsonr(mean_profile.flatten(), test_profile.flatten())[0]
        dp = stats.pearsonr(special_decoded.flatten(), test_profile.flatten())[0]
        if dp > 0.4: # and bp < 0.5
            os.makedirs("profiles", exist_ok=True)
            pname = profiles_viz.fix(df.query('pert_id=="' + str(test_meta_object[1]) + '"')["pert_iname"].tolist()[0])
            profiles_viz.draw_profiles(test_profile, special_decoded, closest_profile, pname,
                                 input_size, "profiles/" + cell_data.test_meta[i][0] + "_" + str(i)
                                 + "_" + str(dp) + "_" + str(bp) + "_" + pname + ".svg")
            profiles_viz.draw_scatter_profiles(test_profile, special_decoded, closest_profile, pname,
                              "profiles/" + cell_data.test_meta[i][0] + "_" + str(i)
                                         + "_" + str(dp) + "_" + str(bp) + "_" +
                                         pname + "_scatter.svg")
        tsne_perts.append(["PC3" if test_meta_object[0] == "MCF7" else "MCF7",
                           df.query('pert_id=="' + str(test_meta_object[1]) + '"')["pert_iname"].tolist()[0]])
        tsne_input.append(closest_profile.flatten())
        tsne_latent.append(encoder.predict(closest_profile).flatten())
        if test_meta_object[0] == "MCF7":
            good_perts.append([test_meta_object[1], bp])
    np.savetxt("../figures_data/tsne_perts.csv", np.array(tsne_perts), delimiter=',', fmt="%s")
    np.savetxt("../figures_data/tsne_input.csv", np.array(tsne_input), delimiter=',')
    np.savetxt("../figures_data/tsne_latent.csv", np.array(tsne_latent), delimiter=',')
    good_perts.sort(key=lambda x: x[1], reverse=True)
    # matrix = np.zeros((len(good_perts), len(good_perts)))
    # for i in range(len(good_perts)):
    #     for j in range(len(good_perts)):
    #         a = cell_data.get_profile_cell_pert(cell_data.test_data, cell_data.test_meta, "MCF7",
    #                                             good_perts[i][0])
    #         b = cell_data.get_profile_cell_pert(cell_data.test_data, cell_data.test_meta, "PC3",
    #                                             good_perts[j][0])
    #         if a is None or b is None:
    #             continue
    #         vector1 = encoder.predict(np.asarray(a))
    #         vector2 = encoder.predict(np.asarray(b))
    #         vpcc = stats.pearsonr(vector1.flatten(), vector2.flatten())[0]
    #         matrix[i][j] = vpcc
    # for i in range(len(good_perts)):
    #     good_perts[i] = df.query('pert_id=="'+str(good_perts[i][0]) + '"')["pert_iname"].tolist()[0]
    # df1 = pd.DataFrame(data=matrix, index=good_perts, columns=good_perts)
    # df1.to_pickle("../figures_data/latent.p")

    print(" Done")
    with open("log.txt", 'a+') as f:
        for key, value in results.items():
            if key == "count":
                continue
            f.write(key + str(value / results["count"]))
            f.write("\n")

    performance = str(results["Our performance is: "] / results["count"]) + "\t" + \
                  str(results["Our correlation is: "] / results["count"]) + "\t" + \
                  str(results["Our multi-performance is: "] / results["count"]) + "\t" + \
                  str(results["Our multi-correlation is: "] / results["count"]) + "\t" + \
                  str(results["closest profile: "] / results["count"]) + "\t" + \
                  str(results["closest profile correlation is: "] / results["count"]) + "\t" + \
                  str(results["Baseline correlation (mean profile): "] / results["count"]) + "\t" + \
                  str(results["Baseline performance (mean profile): "] / results["count"])

    with open("final_result.tsv", 'a+') as f:
        f.write(str(latent_dim) + "\t" + performance) # str(tr_size) + "\t" +
        f.write("\n")

    with open("all_results", 'a+') as f:
        f.write("\n".join(all_results))
        f.write("\n")
