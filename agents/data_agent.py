from agents.base_agent import BaseAgent
import pandas as pd
import numpy as np

class DataAndSignalAgent(BaseAgent):
    def __init__(self, data_path="data/sales_data.csv"):
        super().__init__(name="DataAgent")
        self.data_path = data_path
        self.df = None
        
        # Tools
        self.register_tool(self.load_data)
        self.register_tool(self.detect_anomalies)
        self.register_tool(self.clean_data)
        self.register_tool(self.get_data_summary)
        
        self.set_system_instruction(
            """
            You are the Data and Signal Agent.
            Your job is to load sales data, detect anomalies, and clean the dataset.
            You should:
            1. Load the data.
            2. Check for anomalies using the 'detect_anomalies' tool.
            3. Clean the data if anomalies are found using 'clean_data'.
            4. Provide a summary of the clean data.
            """
        )

    def load_data(self) -> str:
        """Loads the dataset from CSV."""
        try:
            self.df = pd.read_csv(self.data_path)
            return f"Data loaded successfully. Shape: {self.df.shape}. Columns: {list(self.df.columns)}"
        except Exception as e:
            return f"Error loading data: {e}"

    def detect_anomalies(self, threshold: float = 3.0) -> str:
        """
        Detects anomalies using Z-score.
        Args:
            threshold: Z-score threshold (default 3.0).
        """
        if self.df is None: return "Data not loaded."
        
        self.df['z_score'] = (self.df['Sales'] - self.df.groupby('SKU')['Sales'].transform('mean')) / self.df.groupby('SKU')['Sales'].transform('std')
        anomalies = self.df[np.abs(self.df['z_score']) > threshold]
        return f"Detected {len(anomalies)} anomalies."

    def clean_data(self) -> str:
        """Clips anomalies to 3 sigma."""
        if self.df is None: return "Data not loaded."
        
        def clip(group):
            mean = group['Sales'].mean()
            std = group['Sales'].std()
            lower = mean - 3 * std
            upper = mean + 3 * std
            group['Sales_Cleaned'] = group['Sales'].clip(lower, upper)
            return group

        # Fix for FutureWarning: include_groups=False
        # We use reset_index() (drop=False) to restore 'SKU' from the index
        try:
            self.df = self.df.groupby('SKU').apply(clip, include_groups=False).reset_index()
        except TypeError:
            # Fallback for older pandas versions
            self.df = self.df.groupby('SKU').apply(clip).reset_index()
            
        # If 'level_1' or 'index' was created and we don't need it, we could drop it, 
        # but 'SKU' is what we need.
        # Ensure 'SKU' is a column (it should be after reset_index)
        if 'SKU' not in self.df.columns:
             # This shouldn't happen with reset_index() on a groupby('SKU') result
             print(f"[{self.name}] WARNING: SKU column missing after clean. Columns: {self.df.columns}")
        
        # Add date features
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.df['Month'] = self.df['Date'].dt.month
        self.df['Season'] = self.df['Month'].apply(lambda x: 'Winter' if x in [12, 1, 2] else 
                                                 'Spring' if x in [3, 4, 5] else 
                                                 'Summer' if x in [6, 7, 8] else 'Fall')
        
        return "Data cleaned and enriched with Season/Month."

    def get_data_summary(self) -> str:
        """Returns a summary of the cleaned data."""
        if self.df is None: return "Data not loaded."
        if 'Sales_Cleaned' not in self.df.columns: return "Data not cleaned yet."
        
        summary = self.df.groupby('SKU')['Sales_Cleaned'].describe().to_string()
        return f"Data Summary:\n{summary}"

    def run(self, prompt: str = None) -> pd.DataFrame:
        """
        Orchestrates the data cleaning process using the LLM.
        """
        if prompt is None:
            prompt = "Please load the data, check for anomalies, and clean it. Then give me a summary."
        response = super().run(prompt)
        print(f"[{self.name}] Analysis: {response}")
        
        # Fallback for PoC if LLM didn't trigger tools (e.g. no API key)
        if self.df is None:
            print(f"[{self.name}] FALLBACK: Manually loading and cleaning data.")
            self.load_data()
            self.clean_data()
            
        return self.df

if __name__ == "__main__":
    agent = DataAndSignalAgent()
    df = agent.run()
    print(df.head())
