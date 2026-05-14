import unittest
import pandas as pd
import numpy as np

class TestExportLogic(unittest.TestCase):
    def test_marker_row_insertion(self):
        """
        Verify that the marker row is inserted correctly above the sorted data.
        Requirement:
        - Row 0 (Marker): MIN Y=99999, MIN X=Value from Row 1, MAX Y=99999, MAX X=Value from Row 1
        - Row 1 (Data): Max Y value row
        """
        # 1. Create Mock Data (Unsorted)
        data_min = [
            {'Data_Y': 10, 'Data_X': 100},
            {'Data_Y': 1000, 'Data_X': 0.1}, # This should be top
            {'Data_Y': 50, 'Data_X': 50}
        ]
        data_max = [
            {'Data_Y': 5, 'Data_X': 200},
            {'Data_Y': 500, 'Data_X': 0.2}, # This should be top
            {'Data_Y': 20, 'Data_X': 80}
        ]
        
        # 2. Simulate "prepare_smooth_df" and Sorting
        def prepare(data, ly, lx):
            df = pd.DataFrame(data)
            df = df.rename(columns={'Data_Y': ly, 'Data_X': lx})
            return df.sort_values(by=ly, ascending=False).reset_index(drop=True)
            
        df_min = prepare(data_min, 'MIN Y', 'MIN X')
        df_max = prepare(data_max, 'MAX Y', 'MAX X')
        
        # Check Sort
        self.assertEqual(df_min.iloc[0]['MIN Y'], 1000)
        self.assertEqual(df_min.iloc[0]['MIN X'], 0.1)
        
        # 3. Simulate Marker Logic
        val_min_x = df_min['MIN X'].iloc[0]
        val_max_x = df_max['MAX X'].iloc[0]
        
        marker = pd.DataFrame([{
            'MIN Y': 99999, 'MIN X': val_min_x,
            'MAX Y': 99999, 'MAX X': val_max_x
        }])
        
        df_combined = pd.concat([df_min, df_max], axis=1)
        df_final = pd.concat([marker, df_combined], ignore_index=True)
        
        # 4. Assertions
        # Check Row 0 (Marker)
        self.assertEqual(df_final.iloc[0]['MIN Y'], 99999)
        self.assertEqual(df_final.iloc[0]['MAX Y'], 99999)
        self.assertEqual(df_final.iloc[0]['MIN X'], 0.1) # Matches top data
        self.assertEqual(df_final.iloc[0]['MAX X'], 0.2) # Matches top data
        
        # Check Row 1 (Original Top Data)
        self.assertEqual(df_final.iloc[1]['MIN Y'], 1000)
        self.assertEqual(df_final.iloc[1]['MIN X'], 0.1)
        
    def test_empty_data(self):
        """Test robustness with empty data"""
        df_min = pd.DataFrame(columns=['MIN Y', 'MIN X'])
        df_max = pd.DataFrame(columns=['MAX Y', 'MAX X'])
        
        val_min_x = df_min['MIN X'].iloc[0] if not df_min.empty else 0
        val_max_x = df_max['MAX X'].iloc[0] if not df_max.empty else 0
        
        self.assertEqual(val_min_x, 0)
        self.assertEqual(val_max_x, 0)

if __name__ == '__main__':
    unittest.main()
