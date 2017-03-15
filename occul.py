# coding: utf-8
import os
import numpy as np
import pandas as pd
import cPickle as pickle

"""
look at this page:
https://www.coder-note.com/questions/10715965/add-one-row-in-a-pandas-dataframe
"""

def main():
    BWN = 2490.0
    EWN = 2520.0
    HTL = 150; HTR = 220
    UTL = 0; UTR = 100
    wrk_dir = "/home/ju/work_ju/occultation/data"

    #############################
    # preproc(wrk_dir)
    #############################

    file = open(wrk_dir + "/out/data",'rb')
    data = pickle.load(file)
    file.close()

    sorted_data = sorted(data.iteritems(), key = lambda d:d[1]['tanht'], reverse = False)
    keys = [sorted_data[i][0] for i in range(len(sorted_data))]

    file = open(wrk_dir + "/out/df",'rb')
    df = pickle.load(file)
    file.close()

    os.chdir("/home/ju/sciatran/SCIATRAN/Execute-3.3.2")

    #############################
    # valid_data(wrk_dir, data, keys, HTL, HTR, UTL, UTR, BWN, EWN)
    #############################    

    #############################
    control_init(data, keys, L = 0, R = 100)
    #############################

    # import lmfit
    # out_dir = os.path.join(os.getcwd(), "DATA_OUT/intensity_dummy.dat")
    # trans = np.loadtxt(out_dir)[:, 1::]
    from lmfit import minimize, Minimizer, Parameters, Parameter, report_fit
    # lmfit_tanht(wrk_dir, df)
    file = open(wrk_dir + "/out/result",'rb')
    data = pickle.load(file)
    file.close()
    print report_fit(data)

def lmfit_tanht(wrk_dir, df):
    from lmfit import minimize, Minimizer, Parameters, Parameter, report_fit
    
    tanhts = df.columns.values
    params = Parameters()
    for idx in range(tanhts.shape[0]):
        name = "tanht" + str(idx)
        val = tanhts[idx]
        min = val - 10
        max = val + 10
        params.add(name, value = val, min = min, max = max)
    data = df.values
    wn = df.index.values

    ##out = minimize(residual, params, args = (wn, data)) 
    kws  = {'options': {'maxiter':2}}
    minner = Minimizer(residual, params, fcn_args=(wn, data))
    result = minner.minimize()

    file = open(wrk_dir + "/out/result",'wb')
    pickle.dump(result, file, -1)
    file.close() 
    print result

def residual(params, wn, data):
    tanhts = [params[i] for i in params]
    model = modeling(tanhts)

    model = model.ravel()
    data = data.ravel()
    print np.sqrt(np.abs(model**2 - data**2))
    return np.sqrt(np.abs(model**2 - data**2))

def modeling(tanhts):
    tanhts = [tanht.value for tanht in tanhts]
    f = open("control_geom.inp")
    file = [line for line in f.readlines()]
    f.close()
    #--------------------------------------------
    file[100] = str(tanhts)[1: -1] + '\n' # tangent heights
    #--------------------------------------------
    f = open("control_geom.inp", 'w')
    f.writelines(file)
    f.close()
    ##########
    call_RTM()
    ##########
    out_dir = os.path.join(os.getcwd(), "DATA_OUT/intensity.dat")
    trans = np.loadtxt(out_dir)[:, 1::]
    return trans


def valid_data(wrk_dir, data, keys, HTL, HTR, UTL, UTR, BWN, EWN):
    aver_keys = [key for key in keys if HTL < data[key]["tanht"] < HTR]
    aver_spec = np.array([data[key]["spectra"] for key in aver_keys]).mean(axis = 0)
    for key in keys:
        data[key]["spectra"] /= aver_spec
    used_keys = [key for key in keys if UTL < data[key]["tanht"] < UTR]

    wn = data[used_keys[0]]["wavelength"]
    idxs = [np.abs(wn - BWN).argmin(), np.abs(wn - EWN).argmin()]
    wn = wn[idxs[0]: idxs[-1] + 1]
    specs = np.array([data[used_keys[time]]["spectra"][idxs[0]: idxs[-1] + 1] for time in range(len(used_keys))]).T
    df = pd.DataFrame(specs, index = wn, columns = [data[key]["tanht"] for key in used_keys])

    file = open(wrk_dir + "/out/df",'wb')
    pickle.dump(df, file, -1)
    file.close()

def call_RTM():
    os.system("SCIA_unknown_gfortran.exe")

def control_init(data, keys, num = 0, L = -100, R = 200):

    tanhts, azis, zens = [], [], []
    for key in keys:
        pntdata = data[key]
        tanhts.append(str(np.round(pntdata["tanht"], 2)))
        zens.append(str(np.round(pntdata["zen"], 2)))
        azis.append(str(np.round(pntdata["azi"], 2)))
    print os.getcwd()

    f = open("control_geom.inp")
    file = [line for line in f.readlines()]
    f.close()
    # print file[73], file[77] # zenith angles
    # print file[94], file[100] # tangent heights
    # print file[106], file[110] # azimuth angles
    # print len(tanhts), len(azis), len(zens)

    if num != 0:
        tanhts = tanhts[0:num]
        zens = zens[0:num]
        azis = azis[0:num]
    
    idxs = np.intersect1d(np.where(np.array(tanhts).astype(np.float64) > L), np.where(np.array(tanhts).astype(np.float64) < R))
    zens = [zens[idx] for idx in idxs]
    tanhts = [tanhts[idx] for idx in idxs]
    azis = [azis[idx] for idx in idxs]

    file[73] = file[94] = file[106] = str(len(tanhts)) + '\n'
    file[77] = str(zens)[1: -1] + '\n' # zenith angles
    file[100] = str(tanhts)[1: -1] + '\n' # tangent heights
    file[110] = str(azis)[1: -1] + '\n' # azimuth angles

    f = open("control_geom.inp", 'w')
    f.writelines(file)
    f.close()



def preproc(wrk_dir):
    paths = [os.path.join(wrk_dir+ "/raws", path) for path in os.listdir(wrk_dir + "/raws")]
    sci_data = pd.read_excel(os.path.join(wrk_dir, "aux_data/sci_info.xlsx"))
    aux_data = pd.read_excel(os.path.join(wrk_dir, "aux_data/aux_data.xlsx"))

    sci_data["int_timetag"] = [int(round(val)) for val in sci_data["timetag"].values]

    df = pd.DataFrame(columns=("timetag", "lon", "lat", "tanht", "corr_tanht"))
    count = 0
    data = {}
    for path in paths:
        name = int(os.path.basename(path).split(".")[0])
        idx = aux_data.query("blob_oid == @name").index[0]
        timetag = aux_data["acquisitiontime"][idx]
        try:
            idx = sci_data.query("int_timetag == @timetag").index[0]
            lon = sci_data["tplon"][idx]
            lat = sci_data["tplat"][idx]
            zen = sci_data["zenith"][idx]
            azi = sci_data["azimuth"][idx]
            tanht = sci_data["tanht"][idx]
            corr_tanht = sci_data["l2_tanht"][idx]
            # temp = [timetag, lon, lat, tanht, corr_tanht]
            # df.loc[count] = temp
            # count += 1
            temp = np.loadtxt(path)
            temp_ = np.sqrt(temp[:, 1]**2 + temp[:, 2]**2)
            data[str(timetag)] = {"timetag": timetag, "wavelength": temp[:, 0] , "spectra": temp_ , "lon": lon, "lat": lat,
                "zen": zen, "azi": azi, "tanht": tanht, "corr_tanht": corr_tanht}

            file = open(wrk_dir + "/out/data",'wb')
            pickle.dump(data, file, -1)
            file.close()

        except Exception, e:
            # print Exception, e
            continue

def trash():
    # temp = df["corr_tanht"].isnull().values
    # idx = np.where(temp == True)[0]
    # df = df.drop(idx, axis = 0)

    """
    添加pd的方法
    df = pd.DataFrame(columns=('lib', 'qty1', 'qty2', 'aa', 'ss') )
    s2 = pd.Series(temp, index=np.arange(0, 5))
    df2 = pd.Series(temp, index=('lib', 'qty1', 'qty2', 'aa', 'ss')).T
    df.append(df2, ignore_index=True)
    or
    df2 = pd.DataFrame(temp, index=('lib', 'qty1', 'qty2', 'aa', 'ss')).T
    df.append(df2)

    # df = pd.DataFrame(columns=('lib', 'qty1', 'qty2', 'aa', 'ss'))
    # df.loc[i] = temp
    """

if __name__ == '__main__':
    main()
    print "ok."