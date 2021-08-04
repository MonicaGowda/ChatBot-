from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from rasa_sdk import Action
from rasa_sdk.events import SlotSet
import pandas as pd
import json

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from rasa_sdk.events import AllSlotsReset
from rasa_sdk.events import Restarted

import re

ZomatoData = pd.read_csv('zomato.csv')
ZomatoData = ZomatoData.drop_duplicates().reset_index(drop=True)
WeOperate = ['New Delhi', 'Gurgaon', 'Noida', 'Faridabad', 'Allahabad', 'Bhubaneshwar', 'Mangalore', 'Mumbai', 'Ranchi', 'Patna', 'Mysore', 'Aurangabad', 'Amritsar', 'Puducherry', 'Varanasi', 'Nagpur', 'Vadodara', 'Dehradun', 'Vizag', 'Agra', 'Ludhiana', 'Kanpur', 'Lucknow', 'Surat', 'Kochi', 'Indore', 'Ahmedabad', 'Coimbatore', 'Chennai', 'Guwahati', 'Jaipur', 'Hyderabad', 'Bangalore', 'Nashik', 'Pune', 'Kolkata', 'Bhopal', 'Goa', 'Chandigarh', 'Ghaziabad', 'Ooty', 'Gangtok', 'Shimla']

def RestaurantSearch(City,Cuisine):
    TEMP = ZomatoData[(ZomatoData['Cuisines'].apply(lambda x: Cuisine.lower() in x.lower())) & (ZomatoData['City'].apply(lambda x: City.lower() in x.lower()))]
    return TEMP[['Restaurant Name','Address','Average Cost for two','Aggregate rating']]

class ActionSearchRestaurants(Action):
    def name(self):
        return 'action_search_restaurants'

    def run(self, dispatcher, tracker, domain):
        #config={ "user_key":"f4924dc9ad672ee8c4f8c84743301af5"}
        count = 0
        loc = tracker.get_slot('location')
        cuisine = tracker.get_slot('cuisine')
        budget = tracker.get_slot('budget')
        results = RestaurantSearch(City=loc,Cuisine=cuisine)
        response=""
        
        # defalut budget range set to high
        #budget_range = "high" 
        
        # Set the budget scale 
        if budget == "299":
            budget_range = "low"
        elif budget == "700":
            budget_range = "mod"
        elif budget == "701":
            budget_range = "high"
        else:
            budget_range = "low"
        
        
        # Below condition to validate for locations where operations does not exist
        # if loc.lower() not in (string.lower() for string in WeOperate):
        #     response= "Sorry we don't operate in " + loc + " area yet."
        #     dispatcher.utter_message("-----"+response)
            
        # Below condition to validate, If the location doesn't have 5 restaurants, then the bot should not provide any result for that area.
        #elif results.shape[0] < 5:
        #    response= "Sorry! We don't have matching restaurants for " + loc + " location and " +cuisine + " Cusine."
        if (count <=5):
            # Sort results dataframe in decending order of Aggregate rating and ascending order of restaurant name.
            results = results.sort_values(["Aggregate rating", "Restaurant Name"], ascending = (False, True))            
            # Itereate through top 5 results
            for restaurant in results.iterrows():
                restaurant = restaurant[1]
                if((budget_range == "low") and (restaurant['Average Cost for two'] < 300) and (count <= 5)):
                    response=response + F"{count+1}:{restaurant['Restaurant Name']} in {restaurant['Address']} has been rated {restaurant['Aggregate rating']} \n\n" 
                    count = count + 1
                elif((budget_range == "mod") and (restaurant['Average Cost for two']  >= 300) and (restaurant['Average Cost for two'] <= 700) and (count <= 5)):
                    response=response + F"{count+1}:{restaurant['Restaurant Name']} in {restaurant['Address']} has been rated {restaurant['Aggregate rating']} \n\n" 
                    count = count + 1
                elif((budget_range == "high") and (restaurant['Average Cost for two']  > 700) and (count <= 5)):
                    response=response + F"{count+1}:{restaurant['Restaurant Name']} in {restaurant['Address']} has been rated {restaurant['Aggregate rating']}  \n\n" 
                    count = count + 1
                if(count==5):
                    dispatcher.utter_message(response)
                    break
        if(count<5 and count>0):
            response=response + "Sorry! less than 5 restaurants found for " + loc + " location and " +cuisine + " Cusine."
            dispatcher.utter_message(response +"\n\n")
                                
        elif(count==0):
            response = "Sorry, No restaurants found for your criteria"
            dispatcher.utter_message(response)
                            
              
        return [SlotSet('emailbody',response)]
           
    
class ActionSendMail(Action):
    def name(self):
        return 'action_send_mail'

    # def run(self, dispatcher, tracker, domain):
    #     MailID = tracker.get_slot('mail_id')
    #     sendmail(MailID,response)
    #     return [SlotSet('mail_id',MailID)]


    def run(self, dispatcher, tracker, domain):
        from_user = 'chatbot2021.upgrad@gmail.com'
        to_user = tracker.get_slot('email')
        body = tracker.get_slot('emailbody')
        password = 'Chatbot2021*'
        server = smtplib.SMTP('smtp.gmail.com',587)
        server.starttls()
        server.login(from_user, password)
        subject = 'Foodie ChatBot: Your requested list if restaurants'
        msg = MIMEMultipart()
        msg['From'] = from_user
        msg['TO'] = to_user
        msg['Subject'] = subject
        msg.attach(MIMEText(body,'plain'))
        text = msg.as_string()
        server.sendmail(from_user,to_user,text)
        server.close()
        dispatcher.utter_message("Email Sent!")
        
            
class ActionValidateCuisine(Action):
    def name(self):
        return "action_check_cuisine_valid"

    def run(self, dispatcher, tracker, domain):

        cuisine = tracker.get_slot("cuisine")
        cuisine_validity = "valid"

        supported_cuisines = ["american","chinese","italian","mexican","north indian","south indian"]
        
        if cuisine.lower() not in supported_cuisines:
            cuisine_validity = "invalid"
            cuisine = "None"
            dispatcher.utter_message("***Please select from below listed supported cuisines only***")
        else:
            cuisine_validity = "valid"
            cuisine = cuisine            

        
        return [SlotSet("cuisine_validity", cuisine_validity),SlotSet("cuisine", cuisine)]


class ActionValidateLocation(Action):
    def name(self):
        return "action_check_location_valid"

    def run(self, dispatcher, tracker, domain):
        
        loc = tracker.get_slot('location')
        
        if loc.lower() not in (string.lower() for string in WeOperate):
            response= "Sorry we don't operate in " + loc + " area yet."
            location_validity = "invalid"
            loc="None"
            dispatcher.utter_message("-----"+response)
        else:
            location_validity = "valid"
            loc = loc
            
        return [SlotSet("location_validity", location_validity),SlotSet("location", loc)]    
    
class ActionValidateEmail(Action):
    def name(self):
        return "action_check_email_valid"

    def run(self, dispatcher, tracker, domain):
        
        email = tracker.get_slot('email')
        regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
        
        if (re.search(regex, email)):
            email_validity = "valid"
            email = email
            
        else:
            email_validity = "invalid"
            email = "None"
            response= "*** You have entered an invalid email id, please check and re-enter***"
            dispatcher.utter_message(response)
            
        return [SlotSet("email_validity", email_validity),SlotSet("email", email)]      
    
 
class ActionRestarted(Action): 	
    def name(self): 		
        return 'action_restarted' 	
    def run(self, dispatcher, tracker, domain): 
        return[Restarted()] 

class ActionSlotReset(Action): 	
    def name(self): 		
        return 'action_slot_reset' 	
    def run(self, dispatcher, tracker, domain): 		
        return[AllSlotsReset()]           