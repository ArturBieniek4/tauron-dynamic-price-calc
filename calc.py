import datetime, sys

import holidays
pl_holidays = holidays.PL()

UNKNOWN_PRICE_VAL=1.5

#Parse dynamic electricity prices
prices={}
with open("electricity_prices_day_ahead_hourly_all.csv") as f:
    for i, line in enumerate(f):
        if i==0: continue
        line = line.split(",")
        time = line[0]
        date, hour = time.split(" ")
        hour, minute = hour.split(":")
        date = date.split(".")
        time = datetime.datetime(int(date[2]), int(date[1]), int(date[0]), int(hour), 0, 0, 0)
        price = line[1]
        if price=="": price=UNKNOWN_PRICE_VAL
        prices[time]=float(price)

#Parse electricity usage data
usage={}
with open(sys.argv[1]) as f:
    for i, line in enumerate(f):
        if i==0: continue
        line = line.split(";")
        time = line[0]
        energy = line[1]
        date, hour = time.split(" ")
        hour, minute = hour.split(":")
        #shift hour by one back - because Tauron shows "first hour" instead of "an hour that starts at 00:00 and lasts an hour"
        hour = int(hour)-1
        date = date.split("-")
        date = datetime.datetime(int(date[0]), int(date[1]), int(date[2]), hour, 0, 0, 0)
        energy = energy.replace(",", ".")
        usage[date]=float(energy)

def get_distribution():
    sum_high = 0
    sum_mid = 0
    sum_low = 0
    for dt, electricity in usage.items():
        if dt.weekday()>=5 or dt in pl_holidays:
            sum_low+=electricity
        elif dt.hour>=7 and dt.hour<13:
            sum_mid+=electricity
        elif dt.month>=4 and dt.month<=9:
            if dt.hour>=19 and dt.hour<22:
                sum_high+=electricity
            else:
                sum_low+=electricity
        else:
            if dt.hour>=16 and dt.hour<21:
                sum_high+=electricity
            else:
                sum_low+=electricity
    return [sum_high, sum_mid, sum_low]

#Simulate - calculate price by dynamic electricity prices
def calc_netto_energy_cost():
    weighted_sum=0
    sum_energy=0

    for time, electricity in usage.items():
        if time not in prices:
            print("Price not found for time:", time)
            continue
        price=prices[time]

        electricity = round(electricity, 3) # z dokładnością do watogodziny

        #Cena w kWh + składnik cenotwórczy
        cost=electricity*(price/1000+0.0892)

        weighted_sum+=cost
        sum_energy+=electricity

    sum_energy = round(sum_energy) # zaokrąglone do pełnych kWh

    unit_cost = round(weighted_sum/sum_energy, 5)
    
    netto_cost = round(unit_cost*sum_energy, 2)

    return [sum_energy, unit_cost, netto_cost]


energy_amount, unit_energy_cost, netto_energy_cost = calc_netto_energy_cost()
print("Łączne zużycie (zaokrąglone do pełnych kWh):", energy_amount, "kWh")
print("Cena netto za kWh:", unit_energy_cost)
print("Wartość netto:", netto_energy_cost)

vat_cost = round(netto_energy_cost*0.23, 2)
brutto_energy_cost = round(netto_energy_cost + vat_cost, 2)
print("Podatek VAT (zł):", vat_cost)
print("Wartość brutto (zł):", brutto_energy_cost)

distribution_factors = []
distribution_factors.append(7.02) # składnik stały stawki sieciowej
distribution_factors.append(0.33) # stawka opłaty przejściowej

distribution_high, distribution_mid, distribution_low = map(round, get_distribution())

print("Zużycie w szczycie przedpołudniowym:", distribution_mid)
print("Zużycie w szczycie popołudniowym:", distribution_high)
print("Zużycie pozaszczytowe:", distribution_low)

#stawka jakościowa
distribution_factors.append(round(distribution_mid*0.03210, 2))
distribution_factors.append(round(distribution_high*0.03210, 2))
distribution_factors.append(round(distribution_low*0.03210, 2))

#składnik zmienny stawki sieciowej
distribution_factors.append(round(distribution_mid*0.18830, 2))
distribution_factors.append(round(distribution_high*0.33320, 2))
distribution_factors.append(round(distribution_low*0.03490, 2))

#opłata OZE
distribution_factors.append(round(distribution_mid*0.00350, 2))
distribution_factors.append(round(distribution_high*0.00350, 2))
distribution_factors.append(round(distribution_low*0.00350, 2))

#opłata kogeneracyjna
distribution_factors.append(round(distribution_mid*0.00300, 2))
distribution_factors.append(round(distribution_high*0.00300, 2))
distribution_factors.append(round(distribution_low*0.00300, 2))

#stawka opłaty abonamentowej
distribution_factors.append(4.56)

brutto_distribution_factors = [round(factor*1.23, 2) for factor in distribution_factors]

print("Składniki opłaty za dystrybucję (netto | brutto):")
for factor, brutto_factor in zip(distribution_factors, brutto_distribution_factors):
    print(factor, brutto_factor)

brutto_distribution = sum(brutto_distribution_factors)
print("Ogółem wartość za dystrybucję (brutto):", brutto_distribution)

brutto_all_in = brutto_energy_cost + brutto_distribution
print("Łączna opłata za prąd:", brutto_all_in)

avg_all_in = round(brutto_all_in / energy_amount, 2)
print("Średnia cena brutto 1 kWh:", avg_all_in)