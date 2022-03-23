from __future__ import print_function, division
import numpy as np
import random
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from miller_curve_algorithm import ccgFilter
from my_functions import long_date_to_decimal_date, monte_carlo_step2
from my_functions import year_month_todecimaldate
from my_functions import monte_carlo_step1
from my_functions import two_tail_paired_t_test

""" 
 In "heidelberg_intercomparison_cleaned.py",
- Data is imported and cleaned 
- Certain time periods are removed
  - before 1980 for RRL
  - between 1995 and 2005 for RRL
  - between 2009 and 2012 for RRL
  
- Data is smoothed using CCGCV
- Monte Carlo is used to estimate uncertainty of original points
    by curve smoothing 1000 times. 
 - used Paired T-tests to see if the broader datasets and individual 
    time periods are the same/different
 
 
In MyFunctions.py
monte_carlo_step1 returns a randomized array of the Y-data we're interested in, within it's uncertainty
range
monte_carlo_step2 curve smoothes each randomized array of the Y-data. However, the data it returns (for Heidelberg 
and for RRL) are different lengths. I need to do this again so the curve smoother outputs X-data that I SPECIFY. 
Then I can propagate the monte carlo errors directly into paired t-tests. 

GOAL OF THIS FILE: 
Include propogated Monte Carlo error in Paired t-tests
Get Monthly averages without the smooth curve process
 """

""" Define all the functions that I'll be using """


# TODO change n to 10

def monte_carlo_randomization(x_init, fake_x, y_init, y_error, cutoff):
    new_array = y_init  # create a new variable on which we will later v-stack randomized lists
    n = 10  # the amount of times that our loop will go around

    for i in range(0, n):
        empty_array = []
        for j in range(0, len(y_init)):
            a = y_init[j]  # grab the first item in the set
            b = y_error[j]  # grab the uncertainty
            rand = random.uniform(b, b * -1)  # create a random uncertainty within the range of the uncertainty
            c = a + rand  # add this to the number
            empty_array.append(c)  # add this to a list
            # print(len(empty_array))
        new_array = np.vstack((new_array, empty_array))

# CODE WORKS UP TO ABOVE

    template_array = ccgFilter(x_init, y_init, cutoff).getSmoothValue(fake_x)
    for k in range(0, len(new_array)):
        row = new_array[k]  # grab the first row of the data
        smooth = ccgFilter(x_init, row, cutoff).getSmoothValue(fake_x)  #outputs smooth values at my desired times, x
        template_array = np.hstack((template_array, smooth))
    df = pd.DataFrame(template_array)

    mean_array = []
    stdev_array = []
    upper_array = []
    lower_array = []
    for i in range(0, len(template_array)):
        element1 = np.sum(template_array[i])  # grab the first ROW of the dataframe and take the sum
        mean = element1 / len(template_array[i])  # find the mean of all the values from the Monte Carlo
        mean_array.append(mean)  # append it to a new array

        stdev = np.std(template_array[i])
        stdev_array.append(stdev)

        upper = mean + stdev
        lower = mean - stdev
        upper_array.append(upper)
        lower_array.append(lower)

    return new_array, template_array, mean_array, stdev_array, upper_array, lower_array, fake_x

def two_tail_paired_t_test(y1, y1err, y2, y2err):

    # subtract the data from each other
    difference = np.subtract(y1, y2)

    # propogate the errors with sum of squares
    errorprop_step1 = y1err * y1err
    errorprop_step2 = np.sqrt(errorprop_step1)
    errorprop_step2 = list(errorprop_step2)

    errorprop_step3 = y2err * y2err
    errorprop_step4 = np.sqrt(errorprop_step2)
    errorprop_step4 = list(errorprop_step4)

    errorprop_step5 = np.add(errorprop_step2, errorprop_step4)
    errorprop_step6 = errorprop_step5 / len(y1)
    print(errorprop_step6)

    # total =[]
    # for i in range(0, len(errorprop)):
    #     total = errorprop[i] + total
    #     total += errorprop[i]
    # print(total)
    # find the mean
    mean = sum(difference) / len(y1)
    # find the standard error



    # # compute the t-statistic
    # t_stat = mean / se
    # t_stat = np.abs(t_stat)
    # d_of_f = len(x1) + len(x2) - 2
    # # find the degrees of freedom, and the closest number in the table to my degrees of freedom
    # dfx = pd.read_excel(
    #     r'G:\My Drive\Work\GNS Radiocarbon Scientist'
    #     r'\The Science\Stats and Data Analysis\Matlab and Python Files\tables.xlsx',
    #     sheet_name='ttable_adjusted')
    # # print(dfx)
    # # locate where the degrees of freedom is equal to my degrees of freedom:
    # value_crits = dfx['value']
    # value_crits = np.array(value_crits)
    # if d_of_f > 100:
    #     value_crit = 1.98
    # else:
    #     value_crit = value_crits[d_of_f - 1]
    #
    # if t_stat <= value_crit:
    #     result = print('There is NO DIFFERENCE. ' + 'Critical value is ' + str(value_crit) + ' at ' + str(d_of_f) + ' degrees of freedom ' + 'while t-stat = ' + str(t_stat) + ' mean is ' + str(mean))
    # else:
    #     result = print('There IS A DIFFERENCE. ' + 'Critical value is ' + str(value_crit) + ' at ' + str(d_of_f) + ' degrees of freedom' + 'while t-stat = ' + str(t_stat) + ' mean is ' + str(mean))
    return mean


""" IMPORT ALL THE DATA """
# Heidelberg data excel file
heidelberg = pd.read_excel(r'G:\My Drive\Work\GNS Radiocarbon Scientist\The Science\Datasets'
                           r'\heidelberg_cape_grim.xlsx', skiprows=40)
# Baring Head data excel file
baringhead = pd.read_excel(r'G:\My Drive\Work\GNS Radiocarbon Scientist\The Science\Datasets'
                           r'\BHD_14CO2_datasets_20211013.xlsx')

# Clean up the file a little: drop NaN's in the column I'm most interested in
heidelberg = heidelberg.dropna(subset=['D14C'])
heidelberg = heidelberg.loc[(heidelberg['D14C'] > 10)]  # filter out the one outlying measurement around 2019
baringhead = baringhead.dropna(subset=['DELTA14C'])

# Split up the baring head file so that it only takes data after the bomb peak, and removes data between 1995 and 2005
# Will need to keep baring head data split into two for accurate curve smoothing (baringhead1 and baringhead_merged)
baringhead = baringhead.loc[(baringhead['DEC_DECAY_CORR'] > 1980)]  # grab all values after 1980
baringhead = baringhead.loc[(baringhead['DELTA14C_ERR'] > 0)]  # get rid of data where the error flag is -1000
baringhead1 = baringhead.loc[(baringhead['DEC_DECAY_CORR'] < 1994)]
baringhead2 = baringhead.loc[(baringhead['DEC_DECAY_CORR'] > 2006)]

# # cutout 2009-2011 from baringhead2
print('Data between 2009 and 2012 removed')
baringhead2_1 = baringhead2.loc[(baringhead2['DEC_DECAY_CORR'] < 2009)]
baringhead2_2 = baringhead2.loc[(baringhead2['DEC_DECAY_CORR'] > 2012)]
baringhead_merged = pd.merge(baringhead2_1, baringhead2_2, how='outer')  # how = outer Keeps ALL Data

# reset indeces to avoid random errors that crop up
heidelberg = heidelberg.reset_index()
baringhead1 = baringhead1.reset_index()
baringhead2 = baringhead2.reset_index()
baringhead_merged = baringhead_merged.reset_index()

""" extract my variables"""
y_init_heid = heidelberg['D14C']  # Y values from heidelberg dataset
yerr_init_heid = heidelberg['weightedstderr_D14C']  # errors associated with Y values from heidelberg dataset
x_init_heid = heidelberg['Average pf Start-date and enddate']  # x-values from heidelberg dataset
x_init_heid = long_date_to_decimal_date(x_init_heid)  # use a function I wrote the change these values to decimal dates

y_init_bhd1 = baringhead1['DELTA14C']
yerr_init_bhd1 = baringhead1['DELTA14C_ERR']
x_init_bhd1 = baringhead1['DATE_COLL']
x_init_bhd1 = long_date_to_decimal_date(x_init_bhd1)

y_init_bhd2 = baringhead_merged['DELTA14C']  # extracting x's and y's from the merged dataset after 2011 hump removed.
yerr_init_bhd2 = baringhead_merged['DELTA14C_ERR']
x_init_bhd2 = baringhead_merged['DATE_COLL']
x_init_bhd2 = long_date_to_decimal_date(x_init_bhd2)

fake_x_temp = np.linspace(1980, 2020, 480)  # x-data that I will use to solve for each of the smoothed curve functions
df_fake_xs = pd.DataFrame({'x': fake_x_temp})


""" randomize the variables within their measurement uncertainty, 1000 times over (this is the Monte Carlo Part 1) """
fake_x_heidelberg = df_fake_xs.loc[(df_fake_xs['x'] >= min(x_init_heid)) & (df_fake_xs['x'] <= max(x_init_heid))]
fake_x_bhd1 = df_fake_xs.loc[(df_fake_xs['x'] >= min(x_init_bhd1)) & (df_fake_xs['x'] <= max(x_init_bhd1))]
fake_x_bhd2 = df_fake_xs.loc[(df_fake_xs['x'] >= min(x_init_bhd2)) & (df_fake_xs['x'] <= max(x_init_bhd2))]

# def monte_carlo_randomization(x_init, fake_x, y_init, y_error, cutoff):
# returns new_array, template_array, mean_array, stdev_array, upper_array, lower_array, fake_x
h_results = monte_carlo_randomization(x_init_heid, fake_x_heidelberg, y_init_heid, yerr_init_heid, 667)
bhd1_results = monte_carlo_randomization(x_init_bhd1, fake_x_bhd1, y_init_bhd1, yerr_init_bhd1, 667)
bhd2_results = monte_carlo_randomization(x_init_bhd2, fake_x_bhd2, y_init_bhd2, yerr_init_bhd2, 667)

# randomized Monte Carlo data that has been smoothed
h_smoothed = h_results[1]
bhd1_smoothed = bhd1_results[1]
bhd2_smoothed = bhd2_results[1]

# the mean of all the randomized, smoothed data at all x-times that I specified
h_mean = h_results[2]
bhd1_mean = bhd1_results[2]
bhd2_mean = bhd2_results[2]

# the stdev of all the randomized, smoothed data at all x-times that I specified
h_stdev = h_results[3]
bhd1_stdev = bhd1_results[3]
bhd2_stdev = bhd2_results[3]

# the upper/lower error bound of all the randomized, smoothed data at all x-times that I specified
h_upper = h_results[4]
bhd1_upper = bhd1_results[4]
bhd2_upper = bhd2_results[4]
h_lower = h_results[5]
bhd1_lower = bhd1_results[5]
bhd2_lower = bhd2_results[5]
# print(type(bhd2_lower))
# print(type(fake_x_heidelberg))
# print(fake_x_heidelberg)

""" Bring the above data into dataframes for easier filtering for paired t-tests """
df_bhd1 = pd.DataFrame({"date": fake_x_bhd1['x'], "mean": bhd1_mean, "stdev": bhd1_stdev, "upper": bhd1_upper, "lower": bhd1_lower, "key": 1})
df_bhd2 = pd.DataFrame({"date": fake_x_bhd2['x'], "mean": bhd2_mean, "stdev": bhd2_stdev, "upper": bhd2_upper, "lower": bhd2_lower, "key": 2})
df_h = pd.DataFrame({"date": fake_x_heidelberg['x'], "mean": h_mean, "stdev": h_stdev, "upper": h_upper, "lower": h_lower, "key": 3})
#
combine = pd.merge(df_bhd1, df_bhd2, how='outer')
combine = pd.merge(combine, df_h, how='outer')
""" Slice up the data where the datasets overlap so I can do paired t-tests """
early_period_bhd = combine.loc[(combine['key'] == 1) & (combine['date'] >= min(x_init_heid))]  # Baring Head part 1, after heidelberg min
early_period_heid = combine.loc[(combine['key'] == 3) & (combine['date'] <= max(x_init_bhd1))]  # Baring Head part 1, after heidelberg min
late_period_bhd = combine.loc[(combine['key'] == 2) & (combine['date'] <= max(x_init_heid))]  # Baring Head part 1, after heidelberg min
late_period_heid = combine.loc[(combine['key'] == 3) & (combine['date'] >= min(x_init_bhd2))]  # Baring Head part 1, after heidelberg min

""" 
Now - the Monte Carlo errors as associated with exact x values that I have chosen, and y-values that are 
the mean of 1000 monte carlo runs. 

Next: I need to do a t-test for the early period and late period, where I propagate the error associated with each 
point through the t-test. 
"""

""" First test: Early Period v Late Period, the whole dataset"""

y1 = early_period_bhd['mean']
y2 = early_period_heid['mean']
y1err = early_period_bhd['stdev']
y2err = early_period_heid['stdev']
# print(y2err)

two_tail_paired_t_test(y1, y1err, y2, y2err)
# TODO CHECK THAT ERROR PROP WORKS ACCURATELY










































# colors = sns.color_palette("rocket")
# colors2 = sns.color_palette("mako")
#
# size = 2
# fig = plt.figure(1)
# plt.scatter(early_period_bhd['date'], early_period_bhd['mean'], marker='o', label='Baring Head Record Early Period', color=colors[0], s=size)
# plt.scatter(early_period_heid['date'], early_period_heid['mean'], marker='o', label='Heidelberg Early Period', color=colors[1], s=size)
# plt.scatter(late_period_bhd['date'], late_period_bhd['mean'], marker='o', label='Baring Head Record Late Period', color=colors[0], s=size)
# plt.scatter(late_period_heid['date'], late_period_heid['mean'], marker='o', label='Heidelberg late Period', color=colors[1], s=size)
# plt.legend()
# plt.title('Initial Data Plot')
# plt.xlim([1980, 2020])
# plt.ylim([0, 300])
# plt.xlabel('Date', fontsize=14)
# plt.ylabel('\u0394 14CO2', fontsize=14)  # label the y axis
# plt.show()




