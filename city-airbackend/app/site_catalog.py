import pandas as pd

class SiteCatalog:
    """
    Expected Excel columns:
    site_id, Location, City, State
    """

    def __init__(self, xlsx_path: str):
        df = pd.read_excel(xlsx_path)

        required = {"site_id", "City", "Location"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Excel missing required columns: {sorted(list(missing))}")

        df["site_id"] = df["site_id"].astype(str).str.strip()
        df["City"] = df["City"].astype(str).str.strip()
        df["Location"] = df["Location"].astype(str).str.strip()

        if "State" not in df.columns:
            df["State"] = ""

        df["State"] = df["State"].astype(str).str.strip()

        df["_city_norm"] = df["City"].str.lower()

        self.df = df

    # 🔹 Used by frontend (City (State))
    def list_cities(self):
        cities = (
            self.df[["City", "State"]]
            .drop_duplicates()
            .sort_values("City")
        )

        return [
            {
                "city": row["City"],
                "state": row["State"]
            }
            for _, row in cities.iterrows()
        ]

    # 🔹 Used by pipeline
    def get_sites_for_city(self, city: str):
        # City may come as "Delhi (Delhi)"
        clean_city = city.split("(")[0].strip().lower()

        sub = self.df[self.df["_city_norm"] == clean_city]

        records = []

        for _, row in sub.iterrows():
            records.append({
                "site_id": row["site_id"],
                "Location": row["Location"]
            })

        return records

    # 🔹 Used for INFO sheet station list
    def get_station_names_for_city(self, city: str):
        clean_city = city.split("(")[0].strip().lower()
        sub = self.df[self.df["_city_norm"] == clean_city]
        return sub["Location"].dropna().unique().tolist()
