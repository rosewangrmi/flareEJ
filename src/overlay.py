#%%
import sys
sys.path.append('..')
from keys import MyKeys
mykey = MyKeys("../config.ini")

import pandas as pd
import geopandas as gpd
import geopy
from shapely.geometry import Polygon, LineString, Point
import matplotlib.pyplot as plt
import folium

#%%
def calculate_percent_overlay(polygone_df, point_df, point_buffer_distance):

    #crs should be in metres

    #Change flare crs to be in metres
    point_df = point_df.to_crs(polygone_df.crs)


    #create buffer distance
    buffer_distance = point_buffer_distance #we want 5 km
    point_df['buffered_geometry'] = point_df['geometry'].buffer(buffer_distance)


    #replace old point geometry with buffered geometry
    point_sub = point_df[['flare_id','buffered_geometry']].copy(deep=True)
    point_sub.rename(columns={'buffered_geometry':'geometry'}, inplace=True)

    polygone_sub = polygone_df[['block_group_id','geometry']].copy(deep=True)
    
    polygone_sub['area_block'] = polygone_sub.area
    point_sub['area_flare'] = point_sub.area

    #Find intersecting geometry for each flare/bg combination with overlap
    gdf_joined = gpd.overlay(polygone_sub,point_sub, how='intersection')

    # Calculating the areas of the newly-created geometries
    gdf_joined['area_join'] = gdf_joined.area

    # # Calculating the areas of the newly-created geometries in relation 
    # # to the original grid cells
    gdf_joined['fraction_blockgroup_covered_by_flare'] = ((gdf_joined['area_join'] / 
                                                    gdf_joined['area_block']))

    #Some rounding issues may produce more than 100...catch those
    gdf_joined['fraction_blockgroup_covered_by_flare'] = gdf_joined['fraction_blockgroup_covered_by_flare'].apply(lambda x: 1 if x > 1 else x)

    #merge the geometiries from flare and blockgroup back in

    #run test
    # flare_grouped = gdf_joined.groupby('flare_id').agg({'area_joined':'sum',
    #                                     'area_flare':'first'})

    # flare_grouped['flare_coverage'] = flare_grouped['area_joined']/flare_grouped['area_flare']
    return gdf_joined

#%%
def match_geospatial_data(df1, df2):

    #get in same crs
    df2 = df2.to_crs(epsg=3857)
    df1 = df1.to_crs(epsg=3857)
    
    if df1.crs != df2.crs:
        raise ValueError("The two GeoDataFrames do not have the same CRS.")

    # Perform a spatial join between df1 and df2
    matched_df = gpd.sjoin(df1, df2, how="left", op='intersects')

    # Return the new GeoDataFrame
    return matched_df
#%%


if __name__=='__main__':

    #%%
    #crs = EPSG:4326 WGS84 geodetic latitude (degree)
    basin_df = gpd.read_file(f'{mykey.sharepoint}/Data/Final Data/MajorBasins')
    basin_df.rename(columns={'NAME':'basin_name'}, inplace=True)
    basin_sub = basin_df[['basin_name','geometry']].copy(deep=True)
    basin_sub['basin_name'] = basin_sub['basin_name'].fillna('Eagle Ford')
    #%%
    
    #%%
    #import shape files
    #crs = EPSG:3857 WGS84 metre
    block_df = gpd.read_file(f'{mykey.sharepoint}/Data/Final Data/AttributesAdded/AttributesAdded.shp')
    block_df.rename(columns={'OBJECTID':'block_group_id'}, inplace=True)
    #%%
    block_sub = block_df[['block_group_id','geometry']].copy(deep=True)
    #%%

    #crs = EPSG:4326 WGS84 geodetic latitude (degree)
    flare_df = gpd.read_file(f'{mykey.sharepoint}/Data/Final Data/CleanedFlares/CleanedFlares.shp')
    flare_df.rename(columns={'ID 2022':'flare_id'}, inplace=True)

    gdf_joined = calculate_percent_overlay(block_df, flare_df, 5000)

    #export
    gdf_joined.to_file(f'{mykey.sharepoint}/Data/Final Data/flare_blockgroup_overlay.shp')
    gdf_joined.to_csv(f'{mykey.sharepoint}/Data/Final Data/flare_blockgroup_overlay.csv', index=False)

    
    #%%
    basin_blockgroup = match_geospatial_data(block_sub, basin_sub)
    basin_blockgroup.drop(columns=['index_right'], inplace=True)


    # %%
    basin_blockgroup.to_file(f'{mykey.sharepoint}/Data/Final Data/basin_blockgroup_overlay.shp')
    basin_blockgroup[['block_group_id','basin_name']].to_csv(f'{mykey.sharepoint}/Data/Final Data/basin_blockgroup_overlay.csv', index=False)
    # %%
