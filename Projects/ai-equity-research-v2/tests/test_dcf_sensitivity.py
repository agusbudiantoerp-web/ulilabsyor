import unittest
from dcf_sensitivity import run_dcf_sensitivity
from multistage_dcf import project_multistage_dcf

class TestMultiStageSensitivity(unittest.TestCase):
 def setUp(self):
  self.f={"revenue_base":1000.0,"net_debt":80.0,"shares_outstanding":10.0,"current_price":1500.0,"fx_rate":1.0}
  self.a={"high_growth":0.12,"transition_growth":0.08,"stable_growth":0.04,"high_growth_years":2,"transition_growth_years":2,"ebitda_margin":0.20,"da_pct_revenue":0.05,"capex_pct_revenue":0.06,"nwc_pct_revenue":0.11,"tax_rate":0.22,"wacc":0.12,"terminal_growth":0.025}
 def test_base_case_matches_main_dcf(self):
  main=project_multistage_dcf(self.f,self.a,years=5)
  result=run_dcf_sensitivity(self.f,self.a,years=5,wacc_values=[0.10,0.12,0.14],terminal_growth_values=[0.015,0.025,0.035])
  self.assertTrue(result["available"])
  self.assertAlmostEqual(result["base_case"]["intrinsic_value_per_share"],main["intrinsic_value_per_share"])
 def test_higher_wacc_lowers_value(self):
  result=run_dcf_sensitivity(self.f,self.a,years=5,wacc_values=[0.10,0.12,0.14],terminal_growth_values=[0.025])
  values=[row["values"][0.025] for row in result["matrix"]]
  self.assertGreater(values[0],values[1])
  self.assertGreater(values[1],values[2])
 def test_all_invalid_scenarios_return_unavailable(self):
  result=run_dcf_sensitivity(self.f,self.a,years=5,wacc_values=[0.01],terminal_growth_values=[0.02])
  self.assertFalse(result["available"])
  self.assertIsNone(result["base_case"])
  self.assertTrue(all(v is None for row in result["matrix"] for v in row["values"].values()))

if __name__ == "__main__":
 unittest.main()
