from bgdi_mapping import BGDIMapping

# Initialise of the mapping with your CSV file and environment (‘int’ or ‘prod’)
mapping = BGDIMapping(bmd="report.csv", env="int")

# Save the final mapping
mapping.mapping.to_csv("mapping_output.csv", index=False)

# Example: finding duplicates
print("Doublons Layer ID :")
print(mapping.mapping[mapping.mapping["Layer ID"].duplicated()])

print("Doublons Geocat UUID :")
print(mapping.mapping[mapping.mapping["Geocat UUID"].duplicated()])
