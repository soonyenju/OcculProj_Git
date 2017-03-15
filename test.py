# coding: utf-8
import gdal, os, osr, ogr
import numpy as np

def main():
    print os.getcwd()
    os.chdir("/root")
    f = gdal.Open("t.he4")
    sds = f.GetSubDatasets()
    sd = sds[6][0]
    ds = gdal.Open(sd)

    w = ds.RasterXSize
    h = ds.RasterYSize
    b = ds.RasterCount

    u = ds.GetRasterBand(2)
    g = u.ReadAsArray(0, 0, w, h)

    dt = ds.GetVirtualMemArray()

    # for x in dir(gdal):
    #     print x

    # help(gdal.ReprojectImage)
    # help(gdal.Grid)
    help(gdal.GridOptions)
    # help(gdal.InfoOptions)
    # help(gdal.Warp)
    # gdal.Grid("a", g)

    cols = 1440
    rows = 720
    originX = -180
    originY = 90
    pixelWidth = 0.25
    pixelHeight = 0.25

    driver = gdal.GetDriverByName('GTiff')
    newRasterfn = "name.tif"
    outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Float32)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, -pixelHeight))
    print outRaster.GetGeoTransform()
    outband = outRaster.GetRasterBand(1)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(4326)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    h = gdal.GridOptions(options=[], format='GTiff', outputType=gdal.GDT_Float32, width=cols, height=rows, outputBounds=[-180, 90, 180, -90], outputSRS = outRasterSRS)
    gdal.Grid(newRasterfn, g, options = h)
    # gdal.ReprojectImage(newRasterfn, g)

def draw_tif(tiff, name = "scd0d25.tif"):
    cols = 1440
    rows = 720
    originX = -180
    originY = 90
    pixelWidth = 0.25
    pixelHeight = 0.25

    driver = gdal.GetDriverByName('GTiff')
    newRasterfn = name
    outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Float32)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, -pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(tiff)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG("4326")
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()


if __name__ == "__main__":
    main()
    print "ok"
