import csv
import os
import ast

# Define the CSV headers
headers = ['Director', 'Film']

# Create a list to hold all the data
all_data = []

# List all files in the current directory
for file_name in os.listdir('.'):
    # Check if the file name follows the naming convention for directors' film lists
    if file_name.endswith('_film_list.txt'):
        # Extract the director's name from the file name
        director_name = file_name.replace('_film_list.txt', '').replace('_', ' ')
        # Open the text file and read the contents
        with open(file_name, 'r') as file:
            lines = file.readlines()
            for line in lines:
                try:
                    # Convert the string representation of a dictionary to an actual dictionary
                    film_data = ast.literal_eval(line.strip())
                    # Add the data to the all_data list
                    all_data.append([director_name, film_data['film']])
                except (SyntaxError, ValueError):
                    # Handle empty or invalid content
                    print(f"Warning: Skipping invalid line in file {file_name}")

# Write the data to a CSV file
with open('directors_film_list.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(headers)
    writer.writerows(all_data)