#load libraries
library(tidyverse)
library(readr)
library(ggplot2)

#load the scraped data
kamernet <- read_csv("file1.csv")

#data preparation
kamernet <- kamernet %>% filter(!is.na(price)) # remove NA's in price column
kamernet$price <- gsub("[^0-9.]", "", kamernet$price) # in column "price" only keep the numbers
kamernet$area <- gsub("[^0-9.]", "", kamernet$area) #in column "area" only keep the numbers

##convert the price and area columns to numeric
kamernet$price <- gsub("\\.", "", kamernet$price) # Remove "." from price column
kamernet$price <- as.numeric(kamernet$price)
kamernet$area <- as.numeric(kamernet$area)

#data aggregation
## add price per square meter 
kamernet$pricearea <- round((kamernet$price / kamernet$area), 2)

## Count the number of rooms in each city
city_counts <- count(kamernet, city)
city_counts

## how the highest count of rooms in each city
city_counts %>% arrange(desc(n))

##Analysis 1##
# plot the number of rooms in the top 10 count cities
city_counts %>% 
  arrange(desc(n)) %>% 
  head(10) %>% 
  ggplot(aes(x = reorder(city, n), y = n)) + 
  geom_bar(stat = "identity") + 
  geom_text(aes(label = n), vjust = -0.5, size = 3.5) +  # Add text labels
  coord_flip() + 
  labs(title = "Number of rooms in the top 10 count cities", x = "City", y = "Number of rooms") 

# save the plot
ggsave("city_counts.png")

##Analysis 2##
# plot the price per area in the top 10 count cities
# Select the cities
cities <- c("Enschede", "Amsterdam", "Utrecht", "Groningen", "Rotterdam", "Almere", "Heerlen", "Hengelo", "Heemskerk", "Huizen")

kamernet %>%
  filter(!is.na(price), !is.na(area), city %in% cities) %>%  # Filter valid price, area, and selected cities
  mutate(pricearea = price / area) %>%
  group_by(city) %>%
  summarize(avg_pricearea = mean(pricearea)) %>% 
  arrange(desc(avg_pricearea)) %>% 
  ggplot(aes(x = reorder(city, avg_pricearea), y = avg_pricearea)) + 
  geom_bar(stat = "identity") +
  geom_text(aes(label = round(avg_pricearea, 1)), vjust = -0.5, size = 3.5) +
  coord_flip() + 
  labs(title = "Average Price per Area in Selected Cities",
       x = "City", 
       y = "Average Price per Area")

# save the plot above
ggsave("price_area.png")

##Analysis 3##
# average price in the top 10 cities
kamernet %>%
  filter(!is.na(price), city %in% cities) %>%  # Filter valid price and selected cities
  group_by(city) %>%
  summarize(avg_price = mean(price)) %>% 
  arrange(desc(avg_price)) %>% 
  ggplot(aes(x = reorder(city, avg_price), y = avg_price)) + 
  geom_bar(stat = "identity") +
  geom_text(aes(label = round(avg_price, 1)), vjust = -0.5, size = 3.5) +
  coord_flip() + 
  labs(title = "Average Price in Selected Cities",
       x = "City", 
       y = "Average Price")
# save the plot
ggsave("average_price.png")

##Analysis 4##
kamernet <- kamernet %>%
  mutate(has_gedeeld_woonkamer = str_detect(details, "Gedeelde woonkamer")) %>%
  mutate(has_geen_woonkamer = str_detect(details, "Geen woonkamer")) %>%
  mutate(has_prive_woonkamer = str_detect(details, "Privé woonkamer"))

kamernet %>% filter(has_gedeeld_woonkamer)  # Listings with a shared living room
kamernet %>% filter(has_geen_woonkamer) # Listings without a living room
kamernet %>% filter(has_prive_woonkamer) # Listings with a private living room

kamernet %>% 
  group_by(has_gedeeld_woonkamer, has_geen_woonkamer, has_prive_woonkamer) %>%
  s

kamernet %>% 
  group_by(has_gedeeld_woonkamer, has_geen_woonkamer, has_prive_woonkamer) %>%
  summarize(average_price = mean(price)) 

kamernet %>%
  group_by(has_gedeeld_woonkamer, has_geen_woonkamer, has_prive_woonkamer) %>%
  filter(!(has_gedeeld_woonkamer == FALSE & has_geen_woonkamer == FALSE & has_prive_woonkamer == FALSE)) %>% 
  summarize(average_price = mean(price)) %>%
  mutate(category = case_when(
    has_gedeeld_woonkamer == TRUE & has_geen_woonkamer == FALSE & has_prive_woonkamer == FALSE ~ "Gedeelde woonkamer",
    has_gedeeld_woonkamer == FALSE & has_geen_woonkamer == TRUE & has_prive_woonkamer == FALSE ~ "Geen woonkamer",
    has_gedeeld_woonkamer == FALSE & has_geen_woonkamer == FALSE & has_prive_woonkamer == TRUE ~ "Privé woonkamer",
    TRUE ~ paste(has_gedeeld_woonkamer, has_geen_woonkamer, has_prive_woonkamer)  # Construct the category here
  )) %>% 
  mutate(category = factor(category)) %>% 
  ggplot(aes(x = category, y = average_price)) +
  geom_bar(stat = "identity") +
  labs(x = "Living Room Category", y = "Average Price", 
       title = "Average Price by Living Room Category") + 
  theme(axis.text.x = element_text(angle = 45, hjust = 1))

# save the plot
ggsave("living_room_category.png")
