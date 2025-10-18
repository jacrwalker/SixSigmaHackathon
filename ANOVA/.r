# Load necessary packages
install.packages("dplyr")
library(dplyr)

install.packages("tidyverse")
library(tidyverse)

library(ggplot2)
install.packages("ggplot2")

install.packages("car")
library(car)  # for Levene’s test (optional, for assumption checking)

install.packages("magrittr")
library(magrittr)

# Upload the datasets
library(readr)
patient_avg <- read_csv("patient_avg_waits.csv")
scratch_wait <- read_csv("scratch_waiting_times_system.csv")

# ---- Descriptive Statistics ----
# Check variable names
names(patient_avg)
names(scratch_wait)

desc_patient <- patient_avg %>%
  summarise(
    Source = "Patient Avg Waits",
    Median = median(avg_wait_minutes, na.rm = TRUE),
    Min = min(avg_wait_minutes, na.rm = TRUE),
    Max = max(avg_wait_minutes, na.rm = TRUE),
    Range = max(avg_wait_minutes, na.rm = TRUE) - min(avg_wait_minutes, na.rm = TRUE)
  )

desc_system <- scratch_wait %>%
  summarise(
    Source = "System Waits",
    Median = median(average_waiting_period_minutes, na.rm = TRUE),
    Min = min(average_waiting_period_minutes, na.rm = TRUE),
    Max = max(average_waiting_period_minutes, na.rm = TRUE),
    Range = max(average_waiting_period_minutes, na.rm = TRUE) - min(average_waiting_period_minutes, na.rm = TRUE)
  )

descriptive_summary <- bind_rows(desc_patient, desc_system)
print(descriptive_summary)

combined_data <- bind_rows(
  patient_avg %>% select(wait_time = avg_wait_minutes) %>% mutate(Source = "Patient Avg Waits"),
  scratch_wait %>% select(wait_time = average_waiting_period_minutes) %>% mutate(Source = "System Waits")
)

# Run one-way ANOVA
anova_result <- aov(wait_time ~ Source, data = combined_data)
summary(anova_result)

# ---- Optional Visualization with Custom Labels ----

# Relabel groups
combined_data <- combined_data %>%
  mutate(Source = recode(Source,
                         "Patient Avg Waits" = "Current System",
                         "System Waits" = "With C.O.R.G.I"))

# Compute medians
median_values <- combined_data %>%
  group_by(Source) %>%
  summarise(median_wait = median(wait_time, na.rm = TRUE))

# Create the plot
ggplot(combined_data, aes(x = Source, y = wait_time, fill = Source)) +
  geom_boxplot(alpha = 0.7, show.legend = FALSE, width = 0.5) +
  geom_text(
    data = median_values,
    aes(x = Source, y = median_wait, label = paste0("Median: ", round(median_wait, 1), " min")),
    hjust = -1.0,   # move further right
    vjust = 0.4,
    color = "black",
    size = 3        # smaller text
  ) +
  labs(
    title = "Comparison of Waiting Times Between Systems",
    y = "Waiting Time (minutes)",
    x = "Simulation"
  ) +
  theme_minimal(base_size = 13) +
  coord_cartesian(clip = "off") +  # prevent clipping
  theme(
    plot.margin = margin(10, 60, 10, 10),  # more space on right for labels
    axis.text.x = element_text(face = "bold")
  ) +
  scale_fill_manual(values = c(
    "Current System" = "lightblue",
    "With C.O.R.G.I" = "goldenrod"
  ))
#ANOVA CODE
