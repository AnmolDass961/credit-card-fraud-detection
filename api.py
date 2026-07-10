from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Literal, Annotated
import joblib
import shap
import pandas as pd
import numpy as np

artifact  = joblib.load('fraud_detection_model.pkl')
model     = artifact['model']
THRESHOLD = artifact['threshold']

app = FastAPI()

explainer     = shap.TreeExplainer(model.named_steps['xgb'])
feature_names = model.named_steps['preprocessor'].get_feature_names_out()

class UserInput(BaseModel):
    step:          Annotated[int,   Field(..., ge=0, description="Hour step of the simulation")]
    type:          Annotated[str,   Field(..., description="Transaction type")]
    amount:        Annotated[float, Field(..., ge=0, description="Transaction amount")]
    oldbalanceOrg: Annotated[float, Field(..., ge=0, description="Origin balance before transaction")]
    newbalanceOrig: Annotated[float,Field(...,ge=0, description='New Balance after transaction')]
    oldbalanceDest:Annotated[float, Field(..., ge=0, description="Destination balance before transaction")]
    newbalanceDest:Annotated[float, Field(..., ge=0, description="Destination balance after transaction")]


@app.get('/health')
def health():
    return {"status": "ok"}


@app.post('/predict')
def predict(data: UserInput):
    try:
        raw_df = pd.DataFrame([data.model_dump()])
        probability = float(model.predict_proba(raw_df)[0][1])
        prediction  = int(probability >= THRESHOLD)

        input_transformed = model.named_steps['preprocessor'].transform(raw_df)
        shap_values       = explainer(input_transformed)
        feature_impacts   = dict(zip(
            feature_names,
            shap_values.values[0].tolist()
        ))

        if probability >= 0.7:
            risk = "HIGH"
        elif probability >= 0.3:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        return JSONResponse(status_code=200, content={
            'prediction':      prediction,
            'probability':     probability,
            'risk_level':      risk,
            'explanations':    feature_impacts,
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})