import pandas as pd
import numpy as np
import parameters as P
import helper_functions as hf
from unit_conversions_and_mw.feedstock_conversions import cellulose, sugars


io_data = pd.read_csv(P.io_table_physicalunits_path).fillna(0)
water_consumption = hf.csv_dict_list(P.water_consumption_path)
water_withdrawal = hf.csv_dict_list(P.water_withdrawal_path)
# Ethanol produciton functional unit (1 kg of ethanol)
etoh_feed_stream_mass_kg = 1
hhv_methane = 52.2 # MJ/kg



def FinalImpactModel(SP_params, feedstock, model, fuel, ionic_liquid, time_horizon, electircity_mix):
    # Returns a dataframe of of all GHG emissions in the form of kg CO2e per MJ enthanol  or 
    # water impacts in the form of Liters per MJ enthanol per process
    #
    # Args:
    #  SP_params: process specific parameters dictionary
    #  model: string refering to whether the GHG model or the water model is run. Options are:
    #  'buttonGHG', 'buttonConsWater', 'buttonWithWater' for the GHG model, the water consumption model and
    #  the withdrawal model respectively
    
    # Returns:
    #  The net GHG emissions (kg CO2e) for the product life cycle by sector for model = 'buttonGHG'
    #  The net consumption water impacts (liters) for the product life cycle by sector for model = 'buttonConsWater'
    #  The net withdrawal water impacts (liters) for the product life cycle by sector for model = 'buttonWithWater'
    if fuel == 'ethanol': 
        hhv_fuel = 27
        fuel_density = 0.789
    if fuel == '1,8-cineole': 
        hhv_fuel = 46.6
        fuel_density = 0.922
    if fuel == 'Bisabolene': 
        hhv_fuel = 46.68
        fuel_density = 0.879
    if fuel == 'Epi-isozizaene': 
        hhv_fuel = 46.68
        fuel_density = 0.879
    if fuel == 'Limonene': 
        hhv_fuel = 45.04
        fuel_density = 0.841
    if fuel == 'Linalool': 
        hhv_fuel = 42.18
        fuel_density = 0.858
    if fuel == 'Isopentenol': 
        hhv_fuel = 34.67
        fuel_density = 0.81

    catalysts = {
            "alcl3": 1.91,
            "ru": 10,
            "deh_cat": 3.75,
            "PdAC_catalyst": 8.308
        }

    if 'Credits' in SP_params.keys():
        electricityCredits = SP_params['Credits']['electricity_generated']
    else:
        electricityCredits = 0
        
    m = {} 
    selectivities = SP_params.keys()
    new_data = np.zeros([len(selectivities), 1])
    m = pd.DataFrame(new_data, columns=['All'], index=selectivities)
    required_electricity = 0

    SP_params['analysis_params'] = {
                                'time_horizon': time_horizon,
                                'facility_electricity': electircity_mix,
                                'feedstock': feedstock,
                                'fuel': fuel,
                                'electricity_credits': electricityCredits,
                                 }
    SP_params['common'] = {
                            "IL_rail_km": 160,
                            "IL_flatbedtruck_mt_km": 80, 
                            "etoh_distribution_rail": 135, 
                            "etoh_distribution_truck": 50, 
                            "feedstock_distribution_rail": 0,
                            "feedstock_distribution_truck": 80,
                            }

    total_steam = 0
    direct_water_consumption = 0
    direct_water_withdrawal = 0
    required_electricity = 0

    for selectivity in selectivities:
        biorefinery_direct_ghg = 0
        cooled_water_ghg = 0
        steam_ghg = 0
        catalyst_ghg = 0
        y = {}
        y_net = {}
        for item in io_data['products']:
            y.update({item:0})
            y_net.update({item:0})
        if 'ionicLiquid_amount' in SP_params[selectivity].keys():
            ionic_liquid_amount = SP_params[selectivity]['ionicLiquid_amount']
        if 'feedstock.kg' in SP_params[selectivity].keys():
            feedstock_amount = SP_params[selectivity]['feedstock.kg']
        if 'IL_Pretreatment' in SP_params.keys():
            ionic_liquid_amount = SP_params['IL_Pretreatment']['ionicLiquid_amount'] 
        if 'Feedstock_Supply_Logistics' in SP_params.keys():
            feedstock_amount = SP_params['Feedstock_Supply_Logistics']['feedstock.kg'] 
        if 'acid.kg' in SP_params[selectivity].keys():
            if (SP_params[selectivity]['acid'] == 'hcl'):
                y["hcl.kg"] = SP_params[selectivity]['acid.kg']
            elif (SP_params[selectivity]['acid'] == 'h2so4'):
                y["h2so4.kg"] = SP_params[selectivity]['acid.kg']
        if 'ionicLiquid_amount' in SP_params[selectivity].keys():
            if ionic_liquid == 'ChLys':
                y["lysine.us.kg"] = ionic_liquid_amount * 0.58
                y["cholinium.hydroxide.kg"] = ionic_liquid_amount * 0.42
            if ionic_liquid == 'EMIM':
                if model == 'buttonGHG':
                    y["emim_acetate.kg"] = ionic_liquid_amount
                else:
                    y["lysine.us.kg"] = ionic_liquid_amount * 0.58
                    y["cholinium.hydroxide.kg"] = ionic_liquid_amount * 0.42
        if 'cellulase_amount' in SP_params[selectivity].keys():
            y["cellulase.kg"] = SP_params[selectivity]['cellulase_amount']
        if 'csl.kg' in SP_params[selectivity].keys():
            y["csl.kg"] = SP_params[selectivity]['csl.kg']
        if 'feedstock.kg' in SP_params[selectivity].keys():
            if SP_params['analysis_params']['feedstock'] == 'corn_stover':
                y["farmedstover.kg"] = feedstock_amount
            if SP_params['analysis_params']['feedstock'] == 'sorghum':
                y["sorghum.kg"] = feedstock_amount
            if SP_params['analysis_params']['feedstock'] == 'mixed':
                y["sorghum.kg"] = feedstock_amount * 0.4
                y["farmedstover.kg"] = feedstock_amount * 0.4
                y["farmedmiscanthus.kg"] = feedstock_amount * 0.2
                y["switchgrass.kg"] = feedstock_amount * 0.2
        if 'dap.kg' in SP_params[selectivity].keys():
            y["dap.kg"] = SP_params[selectivity]['dap.kg']
        if 'caoh.kg' in SP_params[selectivity].keys():
            y["lime.kg"] = SP_params[selectivity]['caoh.kg'] 
        if 'naoh.kg' in SP_params[selectivity].keys():
            y["naoh.kg"] = SP_params[selectivity]['naoh.kg'] 
        if 'h2.kg' in SP_params[selectivity].keys():
            y["h2.kg"] = SP_params[selectivity]['h2.kg'] 
        if 'ng_input_stream_MJ' in SP_params[selectivity].keys():
            y["naturalgas.MJ"] = SP_params[selectivity]['ng_input_stream_MJ'] * hhv_fuel
        if 'octane_ltr' in SP_params[selectivity].keys():
            y["gasoline.MJ"] = (hf.FuelConvertMJ(SP_params[selectivity]['octane_ltr'], "gasoline", "liter")) / fuel_density

        if selectivity == "Transportation":
            y["rail.mt_km"] = ((ionic_liquid_amount * feedstock_amount/1000) * 
                            SP_params['common']['IL_rail_km']  +
                            (etoh_feed_stream_mass_kg/1000 * SP_params['common']['etoh_distribution_rail'] ) +
                            (feedstock_amount/1000) * 
                            SP_params['common']['feedstock_distribution_rail'] )
            y["flatbedtruck.mt_km"] = (((ionic_liquid_amount * feedstock_amount/1000) * 
                                            SP_params['common']['IL_flatbedtruck_mt_km'] ) +
                                        (etoh_feed_stream_mass_kg/1000 * (
                                            SP_params['common']['etoh_distribution_truck'] )) +
                                        (feedstock_amount/1000) * 
                                            SP_params['common']['feedstock_distribution_truck'] )

        if 'electricity' in SP_params[selectivity].keys():
            required_electricity += SP_params[selectivity]['electricity']
            y["electricity.{}.kWh".format(SP_params['analysis_params']['facility_electricity'])] = (
                                                        SP_params[selectivity]['electricity'])
        if 'cooling_water' in SP_params[selectivity].keys():
            cooled_water_ghg += SP_params[selectivity]['cooling_water'] * hf.CooledWaterCO2kg('cooling_water')
        if 'cooling_water25' in SP_params[selectivity].keys():
            cooled_water_ghg += SP_params[selectivity]['cooling_water25'] * hf.CooledWaterCO2kg('cooling_water25')
        if 'chilled_water' in SP_params[selectivity].keys():
            cooled_water_ghg += SP_params[selectivity]['chilled_water'] * hf.CooledWaterCO2kg('chilled_water')
        if 'steam_low' in SP_params[selectivity].keys():
            steam_ghg += SP_params[selectivity]['steam_low'] * hf.CooledWaterCO2kg('steam_low')
            total_steam += SP_params[selectivity]['steam_low']
        if 'steam_high' in SP_params[selectivity].keys():
            steam_ghg += SP_params[selectivity]['steam_high'] * hf.CooledWaterCO2kg('steam_high')
            total_steam += SP_params[selectivity]['steam_high']
        if 'n.kg' in SP_params[selectivity].keys():
            y["n.kg"] = SP_params[selectivity]['n.kg']
        if 'p.kg' in SP_params[selectivity].keys():
            y["p.kg"] = SP_params[selectivity]['p.kg']
        if 'k.kg' in SP_params[selectivity].keys():
            y["k.kg"] = SP_params[selectivity]['k.kg']
        if 'diesel.MJ' in SP_params[selectivity].keys():
            y["diesel.MJ"] = SP_params[selectivity]['diesel.MJ']    
        if 'alcl3.kg' in SP_params[selectivity].keys():
            if model == 'buttonGHG':
                catalyst_ghg += catalysts['alcl3'] * SP_params[selectivity]['alcl3.kg']
            else:
               y['ammonium.sulfate.kg'] = SP_params[selectivity]['alcl3.kg'] 
        if 'ru.kg' in SP_params[selectivity].keys():
            if model == 'buttonGHG':
                catalyst_ghg += catalysts['ru'] * SP_params[selectivity]['ru.kg']
            else:
               y['steel_domestic.kg'] = SP_params[selectivity]['ru.kg']
        if 'deh_cat.kg' in SP_params[selectivity].keys():
            if model == 'buttonGHG':
                catalyst_ghg += catalysts['deh_cat'] * SP_params[selectivity]['deh_cat.kg']
            else:
               y['manganese.kg'] = SP_params[selectivity]['deh_cat.kg']
        if 'PdAC_catalyst.kg' in SP_params[selectivity].keys():
            if model == 'buttonGHG':
                catalyst_ghg += catalysts['PdAC_catalyst'] * SP_params[selectivity]['PdAC_catalyst.kg']
            else:
               y['char.MJ'] = SP_params[selectivity]['PdAC_catalyst.kg'] * 27 


        if model == 'buttonGHG':

            results_kg_co2e = hf.TotalGHGEmissions(io_data, y,
                                                   biorefinery_direct_ghg, cooled_water_ghg, steam_ghg, catalyst_ghg, SP_params['analysis_params']['time_horizon'])

            results_kg_co2e_dict = results_kg_co2e.set_index('products')['ghg_results_kg'].to_dict()

            hf.AggregateResults(m, results_kg_co2e_dict, selectivity)

            m['All'][selectivity] = m['All'][selectivity] # kg per kg

        elif model == 'buttonConsWater':
            if 'water_direct_consumption' in SP_params[selectivity]:
                direct_water_consumption = SP_params[selectivity]['water_direct_consumption'] 
            else:
                direct_water_consumption = 0

            results_water = hf.TotalWaterImpacts(io_data, y, 
                                               water_consumption, direct_water_consumption)

            results_water_dict = results_water.set_index('products')['liter_results_kg'].to_dict()

            hf.AggregateResults(m, results_water_dict, selectivity)

            m['All'][selectivity] = m['All'][selectivity]/hhv_fuel # converting kg per kg results to g per MJ

        elif model == 'buttonWithWater':
            if 'water_direct_withdrawal' in SP_params[selectivity]:
                direct_water_withdrawal = SP_params[selectivity]['water_direct_withdrawal'] 
            else:
                direct_water_withdrawal = 0

            results_water = hf.TotalWaterImpacts(io_data, y, 
                                               water_withdrawal, direct_water_withdrawal)

            results_water_dict = results_water.set_index('products')['liter_results_kg'].to_dict()

            hf.AggregateResults(m, results_water_dict, selectivity)
 
            m['All'][selectivity] = m['All'][selectivity]/hhv_fuel # converting kg per kg results to g per MJ


        y = {}
        y_net = {}
        y_cred = {}
        for item in io_data['products']:
            y.update({item:0})
            y_net.update({item:0})
            y_cred.update({item:0})

        if model == 'buttonGHG':
            y_net["electricity.{}.kWh".format(SP_params['analysis_params']['facility_electricity'])] = -(
                                                        SP_params['analysis_params']['electricity_credits'])
            y_cred["electricity.{}.kWh".format(SP_params['analysis_params']['facility_electricity'])] = (np.where(
                                                        (required_electricity - SP_params['analysis_params']['electricity_credits'])<=0, 
                                                        required_electricity - SP_params['analysis_params']['electricity_credits'],
                                                        0))
            results_kg_co2e_net = hf.TotalGHGEmissions(io_data, y_net, 
                                                              0, 0, 0, 0,
                                                              SP_params['analysis_params']['time_horizon'])
            results_kg_co2e_cred = hf.TotalGHGEmissions(io_data, y_cred, 
                                                              0, 0, 0, 0,
                                                              SP_params['analysis_params']['time_horizon'])
            results_kg_co2e_dict_net = results_kg_co2e_net.set_index('products')['ghg_results_kg'].to_dict()
            results_kg_co2e_dict_cred = results_kg_co2e_cred.set_index('products')['ghg_results_kg'].to_dict()
            aggregated_data_avg = m.T
            aggregated_data_avg['electricity_generated'] = sum(results_kg_co2e_dict_net.values())
            aggregated_data_avg['electricity_cred'] = sum(results_kg_co2e_dict_cred.values())

            steam_credits = -(total_steam * hf.CooledWaterCO2kg('steam_low'))
            aggregated_data_avg['steam_credits'] = steam_credits
            aggregated_data_avg = aggregated_data_avg * 1000/hhv_fuel
        else:
            aggregated_data_avg = m.T

    
    aggregated_data_avg_plot = aggregated_data_avg[list(reversed(aggregated_data_avg.columns.values))]

    return aggregated_data_avg_plot




