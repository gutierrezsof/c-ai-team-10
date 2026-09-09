# c-ai-team-10

## AI Use Disclosure

ChatGPT was used to format and generate the data dictionaries for the cleaned data sets. Outside of the data dictionaries, the content written is our own.

---

## Overview

This project is themed **"Career Compass."** It is targeted for students who are aiming to enter the job market and looking to explore their dream career.

The problem we are working on addressing is the confusion job seekers face when initially exploring careers.

We currently have the Dash app in presentation mode, where we walk through the steps of a simulated character interested in business, named **"Sammie."**

The intended audience for this app is someone who is looking for a future career or career change.

We organized the pages to work in a step-by-step fashion, with the ending result being a focused breakdown on a specific career role.

---

## Application Pages

### Page 1 — "Career Landscape"

**Question:**  
Which careers are both high-paying and growing?

### Page 2 — "Career Match"

**Question:**  
Which careers offer the best overall combination of salary, growth, and job opportunities based on what matters most to me?

### Page 3 — "Compare Careers"

**Question:**  
What are my top matches for my dream career?

### Page 4 — "Explore Career + Location"

**Question:**  
What does this career look like, and where are the best opportunities?

---

## Run

You will run this Dash app by initially git cloning the `c-ai-team-10` repository.

Once it is successfully cloned:

1. Open the repository in VS Code.
2. Open `app.py`.
3. Run the code.
4. Once running, the terminal will provide a link to the application.
5. Click the link to navigate the Dash app.

---

## Data

We used two **Bureau of Labor Statistics (BLS)** tables as our data sources for this Dash app.

### National-Level Dataset

**Source:**  
**Table 1.2 Occupational Projections, 2025–35, and Worker Characteristics, 2025 (Employment in Thousands)**

https://www.bls.gov/emp/tables/occupational-projections-and-characteristics.htm

### State-Level Dataset

**Source:**  
**BLS Occupational Employment and Wage Statistics (OEWS), May 2025 — State Occupational Employment and Wage Estimates**

https://www.bls.gov/oes/tables.htm

---

## Data Cleaning

We cleaned these files to reduce typos, include only relevant columns, and create score variables for the **"Career Match"** page.

There were 6 occupations that did not have a `national_median_wage`. These occupations are excluded from career rankings that require salary information.

---

## `national_careers.csv`

`national_careers.csv` contains one row per occupation with **831 unique occupation titles**.

### Data Dictionary

**national_occ_title:** The name of the occupation at the national level.

**occ_code:** The Standard Occupational Classification (SOC) code used to uniquely identify each occupation.

**occupation_type:** Identifies the type of occupation record, such as an individual occupation or broader occupational category.

**employment_2025:** Estimated number of people employed in the occupation nationally in 2025.

**employment_2035:** Projected number of people employed in the occupation nationally in 2035.

**growth_pct:** Projected percentage change in employment from 2025 to 2035.

**annual_openings:** Projected average number of job openings for the occupation each year.

**national_median_wage:** National median annual wage for workers in the occupation.

**education:** Typical level of education required to enter the occupation.

**occupation_group:** Broad occupational group that the occupation belongs to.

**salary_score:** Converts `national_median_wage` into a comparable 0–100 score using min-max normalization.

Formula:  
`(wage - minimum wage) / (maximum wage - minimum wage) × 100`

**growth_score:** Converts `growth_pct` into a comparable 0–100 score using min-max normalization.

Formula:  
`(growth - minimum growth) / (maximum growth - minimum growth) × 100`

**openings_score:** Converts `annual_openings` into a comparable 0–100 score using min-max normalization.

Formula:  
`(openings - minimum openings) / (maximum openings - minimum openings) × 100`

---

## `state_careers.csv`

`state_careers.csv` contains one row per state per occupation with **35,224 rows**.

### Data Dictionary

**state:** Two-letter abbreviation for the U.S. state.

**state_name:** Full name of the U.S. state.

**occ_code:** The Standard Occupational Classification (SOC) code used to uniquely identify each occupation.

**occ_title:** The name of the occupation.

**state_employment:** Estimated number of people employed in the occupation within that state.

**jobs_per_1000:** Number of jobs in the occupation for every 1,000 jobs in the state. This helps show how common the occupation is within that state's workforce.

**location_quotient:** Measures how concentrated an occupation is in a state compared with the national average. A value above 1 means the occupation is more concentrated in that state than nationally, while a value below 1 means it is less concentrated.

**state_median_wage:** Median annual wage for workers in the occupation within that state.
