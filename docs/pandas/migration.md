# Pandas 1.x to 2.x Migration Guide

## DataFrame.append()

DataFrame.append() was deprecated in pandas 1.4 and removed in pandas 2.0.

Code using DataFrame.append() should be migrated to pandas.concat().

### Old

df = df.append(new_row)

### New

df = pd.concat([df, new_row], ignore_index=True)

For multiple rows, pandas.concat() should be used to combine DataFrames efficiently.

---

## DataFrame.iteritems()

DataFrame.iteritems() was removed in pandas 2.0.

Use DataFrame.items() instead.

### Old

for column, series in df.iteritems():
    print(column)

### New

for column, series in df.items():
    print(column)