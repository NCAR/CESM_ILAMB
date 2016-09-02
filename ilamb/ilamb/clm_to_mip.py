from subprocess import Popen, PIPE

variables = {
    "burntArea":{'sname': 'area_fraction', 'units': '%', 'clmvr': 'ANN_FAREA_BURNED', 't':1}, 
    "cCwd":{'sname': 'wood_debris_carbon_content', 'units': 'kg--m-2', 'clmvr': 'CWDC', 't':1 },
    "cLeaf":{'sname': 'leaf_carbon_content', 'units': 'kg--m-2', 'clmvr': 'LEAFC', 't':1 },
    "cLitter":{'sname': 'litter_carbon_content', 'units': 'kg--m-2', 'clmvr': 'TOTLITC', 't':1 }, 
    "cMisc":{'sname': 'miscellaneous_living_matter_carbon_content', 'units': 'kg--m-2', 'clmvr': 'STORVEGC', 't':1 }, 
    "cProduct":{'sname': 'carbon_content_of_products_of_anthropogenic_land_use_change', 'units': 'kg--m-2', 'clmvr': 'TOTPRODC', 't':1 }, 
    "cSoilMedium":{'sname': 'medium_soil_pool_carbon_content', 'units': 'kg--m-2', 'clmvr': 'SOIL3C', 't':1 }, 
    "cSoilSlow":{'sname': 'slow_soil_pool_carbon_content', 'units': 'kg--m-2', 'clmvr': 'SOIL4C', 't':1 }, 
    "cSoil":{'sname': 'soil_carbon_content', 'units': 'kg--m-2', 'clmvr': 'TOTSOMC_1m', 't':1 }, 
    "cVeg":{'sname': 'vegetation_carbon_content', 'units': 'kg--m-2', 'clmvr': 'TOTVEGC', 't':1 }, 
    "cWood":{'sname': 'wood_carbon_content', 'units': 'kg--m-2', 'clmvr': 'WOODC', 't':1 }, 
    "evspsblsoi":{'sname': 'water_evaporation_flux_from_soil', 'units': 'kg--m-2--s-1', 'clmvr': 'QSOIL', 't':1 }, 
    "evspsblveg":{'sname': 'water_evaporation_flux_from_canopy', 'units': 'kg--m-2--s-1', 'clmvr': 'QVEGE', 't':1 }, 
    "fFire":{'sname': 'surface_upward_mass_flux_of_carbon_dioxide_expressed_as_carbon_due_to_emission_from_fires_excluding_anthropogenic_land_use_change', 'units': 'kg--m-2--s-1', 'clmvr': 'COL_FIRE_CLOSS', 't':1 }, 
    "fVegLitter":{'sname': 'litter_carbon_flux', 'units': 'kg--m-2--s-1', 'clmvr': 'LITFALL', 't':1 }, 
    "gpp":{'sname': 'gross_primary_productivity_of_carbon', 'units': 'kg--m-2--s-1', 'clmvr': 'GPP', 't':1 }, 
    "hfdsn":{'sname': 'surface_downward_heat_flux_in_snow', 'units': 'W--m-2', 'clmvr': 'FGR', 't':1 }, 
    "lai":{'sname': 'leaf_area_index', 'units': '1', 'clmvr': 'TLAI', 't':1 }, 
    "lwsnl":{'sname': 'liquid_water_content_of_snow_layer', 'units': 'kg--m-2', 'clmvr': 'SNOWLIQ', 't':1 }, 
    "mrfso":{'sname': 'soil_frozen_water_content', 'units': 'kg--m-2', 'clmvr': 'SOILICE', 't':1 }, 
    "mrro":{'sname': 'runoff_flux', 'units': 'kg--m-2--s-1', 'clmvr': 'QRUNOFF', 't':1 }, 
    "mrros":{'sname': 'surface_runoff_flux', 'units': 'kg--m-2--s-1', 'clmvr': 'QOVER', 't':1 }, 
    "mrsos":{'sname': 'moisture_content_of_soil_layer', 'units': 'kg--m-2', 'clmvr': 'SOILWATER_CLM_10CM', 't':1 }, 
    "nbp":{'sname': 'surface_net_downward_mass_flux_of_carbon_dioxide_expressed_as_carbon_due_to_all_land_processes', 'units': 'kg--m-2--s-1', 'clmvr': 'NBP', 't':1 }, 
    "nppLeaf":{'sname': 'net_primary_productivity_of_carbon_accumulated_in_leaves', 'units': 'kg--m-2--s-1', 'clmvr': 'LEAFC_ALLOC', 't':1 }, 
    "npp":{'sname': 'net_primary_productivity_of_carbon', 'units': 'kg--m-2--s-1', 'clmvr': 'NPP', 't':1 }, 
    "nppRoot":{'sname': 'net_primary_productivity_of_carbon_accumulated_in_roots', 'units': 'kg--m-2--s-1', 'clmvr': 'FROOTC_ALLOC', 't':1 }, 
    "nppWood":{'sname': 'net_primary_productivity_of_carbon_accumulated_in_wood', 'units': 'kg--m-2--s-1', 'clmvr': 'WOODC_ALLOC', 't':1 }, 
    "prveg":{'sname': 'precipitation_flux_onto_canopy', 'units': 'kg--m-2--s-1', 'clmvr': 'QINTR', 't':1 }, 
    "ra":{'sname': 'plant_respiration_carbon_flux', 'units': 'kg--m-2--s-1', 'clmvr': 'AR', 't':1 }, 
    "rGrowth":{'sname': 'surface_upward_carbon_mass_flux_due_to_plant_respiration_for_biomass_growth', 'units': 'kg--m-2--s-1', 'clmvr': 'GR', 't':1 }, 
    "rh":{'sname': 'heterotrophic_respiration_carbon_flux', 'units': 'kg--m-2--s-1', 'clmvr': 'HR', 't':1 }, 
    "rMaint":{'sname': 'surface_upward_carbon_mass_flux_due_to_plant_respiration_for_biomass_maintenance', 'units': 'kg--m-2--s-1', 'clmvr': 'MR', 't':1 }, 
    "snc":{'sname': 'surface_snow_area_fraction', 'units': '%', 'clmvr': 'FSNO', 't':1 }, 
    "snd":{'sname': 'surface_snow_thickness', 'units': 'm', 'clmvr': 'SNOWDP', 't':1 }, 
    "snm":{'sname': 'surface_snow_melt_flux', 'units': 'kg--m-2--s-1', 'clmvr': 'QMELT', 't':1 }, 
    "snw":{'sname': 'surface_snow_amount', 'units': 'kg--m-2', 'clmvr': 'H2OSNO', 't':1 }, 
    "tsl":{'sname': 'soil_temperature', 'units': 'K', 'clmvr': 'TSOI', 't':1 }, 
    "tran":{'sname': 'transpiration_flux', 'units': 'kg--m-2--s-1', 'clmvr': 'QVEGT', 't':1 }, 
    "sfcWind":{'sname': 'wind_speed', 'units': 'm--s-1', 'clmvr': 'WIND', 't':1 },
    "hfls":{'sname': 'surface_upward_latent_heat_flux', 'units': 'W--m-2', 'clmvr': 'EFLX_LH_TOT', 't':1 }, 
    "hfss":{'sname': 'surface_upward_sensible_heat_flux', 'units': 'W--m-2', 'clmvr': 'FSH', 't':1 }, 
    "hurs":{'sname': 'relative_humidity', 'units': '%', 'clmvr': 'RH2M', 't':1 },
    "huss":{'sname': 'specific_humidity', 'units': '1', 'clmvr': 'Q2M', 't':1 }, 
    "prsn":{'sname': 'snowfall_flux', 'units': 'kg--m-2--s-1', 'clmvr': 'SNOW', 't':1 }, 
    "ps":{'sname': 'surface_air_pressure', 'units': 'Pa', 'clmvr': 'PBOT', 't':1 }, 
    "rlds":{'sname': 'surface_downwelling_longwave_flux_in_air', 'units': 'W--m-2', 'clmvr': 'FLDS', 't':1 }, 
    "rlus":{'sname': 'surface_upwelling_longwave_flux_in_air', 'units': 'W--m-2', 'clmvr': 'FIRE', 't':1 }, 
    "rsds":{'sname': 'surface_downwelling_shortwave_flux_in_air', 'units': 'W--m-2', 'clmvr': 'FSDS', 't':1 }, 
    "rsus":{'sname': 'surface_upwelling_shortwave_flux_in_air', 'units': 'W--m-2', 'clmvr': 'FSR', 't':1 }, 
    "tas":{'sname': 'air_temperature', 'units': 'K', 'clmvr': 'TSA', 't':1 }, 
    "cSoilFast":{'sname': 'fast_soil_pool_carbon_content', 'units': 'kg--m-2', 'clmvr': 'SOIL1C', 't':1 }, 
    "fLuc":{'sname': 'surface_net_upward_mass_flux_of_carbon_dioxide_expressed_as_carbon_due_to_emission_from_anthropogenic_land_use_change', 'units': 'kg--m-2--s-1', 'clmvr': 'LAND_USE_FLUX', 't':1 }, 
    "tws":{'sname': 'total_water_storage', 'units': 'kg--m-2', 'clmvr': 'TWS', 't':1 },

    "mrlsl":{'sname': 'moisture_content_of_soil_layer', 'units': 'kg--m-2', 'clmvr': 'SOILLIQ--SOILICE', 't':2 }, 
    "mrso":{'sname': 'soil_moisture_content', 'units': 'kg--m-2', 'clmvr': 'SOILICE--SOILLIQ', 't':2 },
    "pr":{'sname': 'precipitation_flux', 'units': 'kg--m-2--s-1', 'clmvr': 'RAIN--SNOW', 't':2 },

    "cRoot":{'sname': 'root_carbon_content', 'units': 'kg--m-2', 'clmvr': 'FROOTC--LIVE_ROOTC--DEAD_ROOTC', 't':3 }, 
    "fLitterSoil":{'sname': 'carbon_mass_flux_into_soil_from_litter', 'units': 'kg--m-2--s-1', 'clmvr': 'LITR1C_TO_SOIL1C--LITR2C_TO_SOIL2C--LITR3C_TO_SOIL3C', 't':3 }, 
    "sootsn":{'sname': 'soot_content_of_surface_snow', 'units': 'kg--m-2', 'clmvr': 'SNOBCMSL--SNODSTMSL--SNOOCMSL', 't':3 }, 
    "evspsbl":{'sname': 'water_evaporation_flux', 'units': 'kg--m-2--s-1', 'clmvr': 'QSOIL--QVEGE--QVEGT', 't':3 }
}


def run_mip(globals, cases, scomm):

    # Partition the variables across the ranks
    lvariables = scomm.partition(variables.keys(), func=partition.Duplicate(), involved=True)

    for k,case in cases.iteritems():
        if case['CONVERT_TO_CMIP']:
            for vn,val in lvariables.iteritems():

                cmd = './clm_to_mip '+case['MODEL']+' '+case['EXPERIMENT']+' '+case['YEARS']+' '+vn+' '+val['sname']+' '+val['units']+' '+val['clmvr']+' '+str(val['t'])+' '+case['MIP_OUTPUT_PATH']
                print cmd
                try:
                    pipe = Popen(cmd, shell=True)
                    pipe.wait()
                except OSError as e:
                    print('Failure while trying to run clm_to_mip')
                    print('    {0} - {1}'.format(e.errno, e.strerror))
   
