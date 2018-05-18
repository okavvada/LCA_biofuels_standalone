import csv
import pandas as pd
import numpy as np
import parameters as P

def csv_dict_list(variables_file):
    mydict = {}
    reader = csv.reader(open(variables_file, "rU"))
    for i, rows in enumerate(reader):
        if i == 0: continue
        k = rows[0]
        v = rows[1]
        try:
            value = float(v)
        except ValueError:
            value = str(v)
        mydict[k] = value
    return mydict


def FuelConvertMJ(num, fuel_name, unit):
    # Computes the equivalent MJ (HHV) for kg or liters of a
    # fuel-type material
    #
    # Args:
    #  num: Physical quantity of material in whatever input unit is chosen
    #       (numeric)
    #  fuel_name: String name of the fuel material in all lower-case letters.
    #  unit: String abbreviated name of unit in which the input is measured in
    #        (num) and must be either volume or mass. Must enter units that the
    #        udunits2 package can handle. See documentation here:
    #        http://cran.r-project.org/web/packages/udunits2/udunits2.pdf
    #
    # Returns:
    #  The equivalent MJ (HHV) of num quantity of the fuel material denoted by 
    #  fuel_name  
    #
    # Read in two files:
    # 1) list of fuels with corresponding MJ HHV by liter and kg;
    # 2) file with all possible aliases for each fuel that can be entered by user
    energy_content = pd.read_csv(P.energy_content_path)  # Import conversion table
    aliases = csv_dict_list(P.fuel_aliases_path) # Import table of aliases for fuels and units
    #
    # Check to make sure units entered are valid and detect whether it's a unit of 
    # mass or volume
    # Check if units are valid and, if so, convert num to kg or liter. 
    if unit != "kg" and unit != "liter":
        print("Invalid unit entered. Please use only kg or liters") 
        return

    #
    # Pull official fuel name from list of aliases and lookup energy content to 
    # calculate final HHV in MJ
    # Takes any number of potential fuel aliases from user input and returns 
    # official fuel name for calculations
    unit = unit+"_hhv"
    if fuel_name in aliases.keys():
        fuel =  aliases[fuel_name]
    elif fuel_name in aliases.values():
        fuel =  fuel_name
    else:
        print ("fuel not found")
        return

    content_MJ = energy_content[energy_content['Fuel'] == fuel][unit].iloc[0]
    if content_MJ == "N/A":
        print ("Invalid unit entered. You may not enter a unit of volume for solid fuels")
    else:
    # liter column of data frame requires that the output be converted to a 
    # character, then to numeric.  Converting directly to numeric doesn't work 
    # because the column is a combination of numbers and strings.
        energy_MJ = num * content_MJ  
    return energy_MJ

def FuelCO2kg(MJ_fuel_in, fuel_type):
    # Provides the fossil CO2 emissions (kg) for combustion of a given MJ equivalent
    # of fuel combusted
    #
    # Args:
    #  MJ_fuel_in: total MJ of fuel (HHV) to be combusted
    #  fuel_type: string indicating the fuel type (ethanol, gasoline, diesel) 
    adj = (12+16*2)/12 # Calculates CO2 based on carbon fraction
    #Assume alcohols are completely biomass-derived
    # Numeric coefficients carbon emissions per MJ of fuel
    fuels = {
        'ethanol': 0*adj,
        'n_butanol': 0*adj,
        'iso_butanol': 0*adj,
        'methanol': 0*adj,
        'gasoline': 0.01844452*adj,
        'diesel': 0.01895634*adj,
        'lignite': 0.03901754*adj,
        'anthracite': 0.0456817*adj,
        'coal': 0.02447264*adj,
        'bituminous': 0.03493306*adj,
        'subbituminous': 0.02149727*adj,
        'wood': 0*adj,
        'herbaceousbiomass': 0*adj,
        'cornstover': 0*adj,
        'forestresidue': 0*adj,
        'bagasse': 0*adj,
        'hydrogen': 0*adj,
        'rfo': 0.01885208*adj,
        'naturalgas': 0.01370544*adj,
        'naphtha': 0.01758201*adj,
        'refgas': 0.01725027*adj,
        'crude': 0.01925017*adj,
        'biochar': 0*adj,
        'lignin': 0*adj,
        'ethylene': 0.01683809*adj,
        'propene': 0.01755613*adj,
        'butane': 0.01827829*adj,
        'petrobutanol': 0.01961145*adj,
        'petrohexanol': 0.01812604*adj}

    if fuel_type in fuels.keys():
        fuel_CO2 = MJ_fuel_in * fuels[fuel_type]
    else:
        print ("fuel not found")
        return
    return fuel_CO2

def CooledWaterCO2kg(cooled_type):
    # Provides the fossil CO2 emissions (kg) for cooling water or heating steam
    # of a given volume equivalent
    #
    # Args:
    #  cooled_type: string indicating the water type (cooling_water, chilled_water, 
    # steam_low, steam_high) 
    
    # Numeric coefficients carbon emissions per L of water
    waters = {
        'cooling_water': 0.00024,
        'chilled_water': 0.00046,
        'cooling_water25': 0.00024,
        'steam_low': 0.32,
        'steam_high': 0.32}

    if cooled_type in waters.keys():
        water_CO2 = waters[cooled_type]
    else:
        print ("water not found")
        return
    return water_CO2


def GHGImpactVectorSum(time_horizon):
    # Computes an impact vector equal to the total kg co2 equivalents per physical 
    # output unit for each sector
    #
    # Args:
    #  co2.filepath: csv file path for co2 impact vector (kg/physical output unit)
    #  ch4.filepath: csv file path for ch4 impact vector (kg/physical output unit)
    #  n2o.filepath: csv file path for n2o impact vector (kg/physical output unit)
    #  time.horizon: number of years used for time horizon of IPCC factors - 
    #   default is 100 years, can also to 20
    # Returns:
    #  The total kg co2e for each sector in a vector form
    filepaths = [P.co2_filepath, P.ch4_filepath, P.n2o_filepath]
    # IPCC 100-year multipliers for different GHGs to normalize to CO2e
    ipcc_values = {'ipcc_ch4_100': 28,  
                 'ipcc_ch4_20': 72, 
                 'ipcc_n2o_100': 298,  
                 'ipcc_n2o_20': 289}
    ipcc_multipliers = [1, ipcc_values["ipcc_ch4_{}".format(time_horizon)], ipcc_values["ipcc_n2o_{}".format(time_horizon)]]

    ghg_total_kg = 0

    for x in range(3):
        impact = pd.read_csv(filepaths[x]).loc[:,'r']
        impact *= ipcc_multipliers[x]
        ghg_total_kg = ghg_total_kg + impact

    return ghg_total_kg


def IOSolutionPhysicalUnits(A, y):
    # Solves for total requirements from each sector in in physical units
    #
    # Args:
    #  A: input-output vector in physical units
    #  y: direct requirements vector
    # 
    # Returns:
    #  The total (direct + indirect) requirements by sector
    num_sectors = A.shape[1] 
    I = np.eye(A.shape[1])
    solution = np.linalg.solve((I - A), y)
    return solution


def TotalGHGEmissions(io_data, y, biorefinery_direct_ghg, cooled_water_ghg, steam_ghg, catalysts, time_horizon):
    # Returns a vector of of all GHG emissions in the form of kg CO2e
    #
    # Args:
    #  A: input-output vector in physical units ratios
    #  y: direct requirements vector in physical units
    #  co2.filepath: filepath to csv file containing kg CO2/kg output for 
    #   each sector
    #  ch4.filepath: filepath to csv file containing kg CH4/kg output for 
    #   each sector
    #  n2o.filepath: filepath to csv file containing kg N2O/kg output for 
    #   each sector
    #  time.horizon: number of years used for time horizon of normalized GHG 
    #   forcing
    #  biorefinery.direct.ghg: kg fossil CO2e emitted directly at the biorefinery
    #  combustion.direct.ghg: kg fossil CO2e emitted during product combustion/
    #   end-of-life.  Only applicable where some fossil carbon is in product
    #   or there is net biogenic carbon sequestration
    # Returns:
    #  The net GHG emissions (kg CO2e) for the product life cycle by sector

    A = io_data.drop(['products'],1).values.T
    y_array = []
    for item in io_data['products']:
        y_array.append(y[item])

    io_ghg_results_kg = IOSolutionPhysicalUnits(A, y_array) * GHGImpactVectorSum(time_horizon)
    io_ghg_results_kg = np.append(io_ghg_results_kg,[biorefinery_direct_ghg, cooled_water_ghg, steam_ghg, catalysts])
    rownames = np.append(io_data.products.values, ['direct', 'cooled_water_and_steam', 'steam_ghg', 'catalysts'])
    io_ghg_results_kg_df = pd.DataFrame(io_ghg_results_kg, columns = ['ghg_results_kg'])
    io_ghg_results_kg_df['products'] = rownames
    return io_ghg_results_kg_df


def TotalWaterImpacts(io_data, y, water_consumption, biorefinery_direct_consumption): 
    # Returns a vector of of all water consumption in the form of liters of water
    #
    # Args:
    #  A: input-output vector in in physical units ratios
    #  y: direct requirements vector in in physical units
    #  water.consumption.filepath: filepath to csv file containing liters 
    #   water consumed/kg output for each sector
    #  biorefinery.direct.water.consumption: liters water consumed directy at the 
    #   biorefinery
    # Returns:
    #  The net water consumption (liters water) for the product life cycle by sector
    A = io_data.drop(['products'],1).values.T
    y_array = []
    water_consumption_array = []
    for item in io_data['products']:
        y_array.append(y[item])
        water_consumption_array.append(water_consumption[item])

    io_water_consumption_results_kg = IOSolutionPhysicalUnits(A, y_array) * water_consumption_array

    results_liter_water_consumption = np.append(io_water_consumption_results_kg, biorefinery_direct_consumption)
    rownames = np.append(io_data.products.values, 'direct')
    io_water_results_kg_df = pd.DataFrame(results_liter_water_consumption, columns = ['liter_results_kg'])
    io_water_results_kg_df['products'] = rownames

    return io_water_results_kg_df


def AggregateResults(m, results_kg_co2e, selectivity):
    m['All'][selectivity] = sum(results_kg_co2e.values())


