import rasterio 
import rasterio.plot

with rasterio.open('data/DEU_cov/DEU_cov.vrt') as raster_vrt:
    rasterio.plot.show(raster_vrt)