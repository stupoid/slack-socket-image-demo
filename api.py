import random
from typing import Literal, Optional

import numpy as np
import pandas as pd
import plotly.express as px
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


def get_df(
    country: str = "any",
    column: Optional[Literal["lifeExp", "pop", "gdpPercap"]] = None,
) -> pd.DataFrame:
    df = px.data.gapminder()
    if country == "any":
        country: str = np.random.choice(df.country.unique())

    country_df = df.query(f"country=='{country.capitalize()}'")
    while country_df.empty:
        country = np.random.choice(df.country.unique())
        country_df = df.query(f"country=='{country.capitalize()}'")

    if column is None:
        column = random.choice(["lifeExp", "pop", "gdpPercap"])  # type: ignore

    return country_df[["country", "year", column]]


@app.get("/df/{country}.{format}")
def generate_plot(
    format: Literal["png", "jpg"],
    df: pd.DataFrame = Depends(get_df),
):
    country = df["country"].iloc[0]
    del df[df.columns[0]]
    fig = px.line(
        df, x=df.columns[0], y=df.columns[1], title=f"{df.columns[1]} in {country}"
    )
    img_bytes = fig.to_image(format=format)
    return Response(content=img_bytes, media_type=f"image/{format}")


@app.get("/df/{country}")
def get_country_data(df: pd.DataFrame = Depends(get_df)):
    return df.to_dict()


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}
