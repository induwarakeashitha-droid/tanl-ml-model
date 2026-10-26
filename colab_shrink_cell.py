# Paste this into a NEW cell at the end of your Colab notebook and run it.
# Run all the cells above it first (Runtime > Run before).

import joblib, os, sys, numpy, pandas, sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error


def small_rf():
    return RandomForestRegressor(n_estimators=60, max_depth=14, min_samples_leaf=20,
                                 n_jobs=-1, random_state=0)


test_model = small_rf().fit(X_train, y_train)
print("big model   MAE:", round(mean_absolute_error(y_test, pred_rf), 4))
print("small model MAE:", round(mean_absolute_error(y_test, test_model.predict(X_test)), 4))
print("baseline    MAE:", round(mean_absolute_error(y_test, pred_base), 4))

final_small = small_rf().fit(X, y)
bundle_small = {"model": final_small, "features": FEATURES, "horizon_days": HORIZON,
                "tanks": tanks.drop(columns="cell").to_dict("index")}
joblib.dump(bundle_small, "tank_model.pkl", compress=3)

print(round(os.path.getsize("tank_model.pkl") / 1e6, 1), "MB")
print("\nPython", sys.version.split()[0])
print("\nPut these 3 lines in requirements.txt:")
print(f"numpy=={numpy.__version__}\npandas=={pandas.__version__}\nscikit-learn=={sklearn.__version__}")

files.download("tank_model.pkl")
