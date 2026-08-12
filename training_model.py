import os
import joblib
import pandas as pd
from xgboost import XGBClassifier
from sklearn.preprocessing import PowerTransformer
from sklearn.model_selection import train_test_split
# loading the dataset

df=pd.read_csv(r"C:\Users\CHIRNAJIV ZOPE\Downloads\Chirag Industry\Axle lock cases in locomotives\locomotive_axle_lock_python_sim.csv")


# selecting input and output 

x=df.drop(columns=["axle_lock_label","time_s","axle1_speed_noisy"])
y=df["axle_lock_label"]

# splitting into train and test

x_train,x_test,y_train,y_test=train_test_split(x,y,test_size=0.2,random_state=42,stratify=y)

# performing the scaling and convert data in to normal distribution 

transformer = PowerTransformer(method='yeo-johnson')
X_train_transformed = transformer.fit_transform(x_train)
X_test_transformed = transformer.transform(x_test)

# loading the model

model=XGBClassifier(n_estimators=100,max_depth=4,random_state=42)
model.fit(X_train_transformed,y_train)

# 1. Create a "models" directory if it doesn't already exist
os.makedirs("models", exist_ok=True)

# 2. Save the XGBoost model natively as a JSON fiale
joblib.dump(model, "models/axle_lock_xgb.joblib")

# 3. Save the fitted PowerTransformer using joblib
joblib.dump(transformer, "models/power_transformer.joblib")

print("Both the model and transformer have been saved successfully in the 'models/' directory!")