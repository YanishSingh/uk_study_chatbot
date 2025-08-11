# actions.py
import json
import requests
from pathlib import Path
from typing import Any, Text, Dict, List
import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load API key for ChatGPT integration

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict

# Base directory for your JSON data (two levels up to backend/university_data)
DATA_DIR = Path(__file__).resolve().parents[2] / "university_data"

# Set OpenAI API key (you'll need to set this in your environment)
openai.api_key = os.getenv("OPENAI_API_KEY")  # Uncomment when you have the key


class ValidateStudentProfileForm(FormValidationAction):
    """Custom form validation for student profile"""

    def name(self) -> Text:
        return "validate_student_profile_form"

    def validate_gpa(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate GPA input with percentage conversion support"""
        
        try:
            # Get the raw user input for better parsing
            user_message = tracker.latest_message.get('text', '').lower()
            
            # Debug logging
            print(f"DEBUG: Validating GPA input - user_message: '{user_message}', slot_value: '{slot_value}'")
            
            # Try to extract GPA or percentage from the message using various patterns
            import re
            
            # Percentage patterns - check first as they're more specific
            percentage_patterns = [
                r'(\d+\.?\d*)\s*%',  # "70%"
                r'(\d+\.?\d*)\s*percent',  # "70 percent"
                r'(\d+\.?\d*)\s*percentage',  # "70 percentage"
                r'it\'?s\s*(\d+\.?\d*)\s*%',  # "it's 70%"
                r'my\s*percentage\s*(?:is\s*)?(\d+\.?\d*)',  # "my percentage is 70"
                r'percentage\s*(?:is\s*)?(\d+\.?\d*)',  # "percentage is 85"
            ]
            
            # GPA patterns
            gpa_patterns = [
                r'(\d+\.?\d*)\s*gpa',
                r'gpa\s*(?:is\s*)?(\d+\.?\d*)',
                r'it\'?s\s*(\d+\.?\d*)',
                r'my\s*gpa\s*(?:is\s*)?(\d+\.?\d*)',
                r'(\d+\.\d+)',     # Decimal number specifically (check before single numbers)
                r'(\d+)\s*\.\s*(\d+)',  # Handle tokenized decimals like "2 . 8"
                r'^(\d+\.?\d*)$',  # Just a number (check last to avoid conflicts)
            ]
            
            gpa = None
            is_percentage = False
            original_percentage = None
            
            # First try the slot_value as provided
            if slot_value is not None:
                try:
                    potential_gpa = float(slot_value)
                    # If it's a large number, assume it's a percentage
                    if potential_gpa > 4.0 and potential_gpa <= 100:
                        is_percentage = True
                        original_percentage = potential_gpa
                        gpa = self._convert_percentage_to_gpa(potential_gpa)
                        print(f"DEBUG: Slot value {potential_gpa} treated as percentage, converted to GPA {gpa}")
                    elif 0.0 <= potential_gpa <= 4.0:
                        gpa = potential_gpa
                        print(f"DEBUG: Slot value {potential_gpa} treated as GPA")
                    else:
                        print(f"DEBUG: Slot value {potential_gpa} out of valid ranges")
                except (ValueError, TypeError):
                    print(f"DEBUG: Could not convert slot_value '{slot_value}' to float")
                    pass
            
            # Check for percentage patterns first
            if gpa is None:
                for pattern in percentage_patterns:
                    match = re.search(pattern, user_message)
                    if match:
                        try:
                            percentage = float(match.group(1))
                            if 0 <= percentage <= 100:
                                gpa = self._convert_percentage_to_gpa(percentage)
                                is_percentage = True
                                original_percentage = percentage
                                print(f"DEBUG: Found percentage {percentage}%, converted to GPA {gpa}")
                                break
                            else:
                                print(f"DEBUG: Percentage {percentage} out of valid range (0-100)")
                        except (ValueError, TypeError):
                            continue
            
            # If no percentage found, try GPA patterns
            if gpa is None:
                for pattern in gpa_patterns:
                    match = re.search(pattern, user_message)
                    if match:
                        try:
                            if len(match.groups()) > 1:  # Handle "2 . 8" pattern
                                gpa = float(f"{match.group(1)}.{match.group(2)}")
                                print(f"DEBUG: Found tokenized decimal pattern: {match.group(1)}.{match.group(2)}")
                            else:
                                potential_gpa = float(match.group(1))
                                # Be more careful about treating numbers as percentages
                                # Only treat as percentage if it's clearly out of GPA range
                                if potential_gpa > 4.0 and potential_gpa <= 100:
                                    # Ask for clarification instead of assuming
                                    dispatcher.utter_message(
                                        text=f"I see you entered '{potential_gpa}'. Is this a percentage (like {potential_gpa}%) or did you mean something else? Please clarify with '%' for percentage or provide your GPA on a 0.0-4.0 scale."
                                    )
                                    return {"gpa": None}
                                elif potential_gpa <= 4.0:
                                    gpa = potential_gpa
                                    print(f"DEBUG: Found GPA: {potential_gpa}")
                                else:
                                    print(f"DEBUG: Number {potential_gpa} too large for GPA or percentage")
                                    continue
                            break
                        except (ValueError, TypeError, IndexError):
                            continue
                            
            # Special case: check if message contains separated decimal like "2 8"
            if gpa is None:
                tokens = user_message.split()
                for i, token in enumerate(tokens):
                    if token.isdigit() and i + 1 < len(tokens):
                        next_token = tokens[i + 1]
                        if next_token.isdigit() and len(next_token) == 1:
                            try:
                                combined_gpa = float(f"{token}.{next_token}")
                                if combined_gpa <= 4.0:
                                    gpa = combined_gpa
                                    print(f"DEBUG: Found separated tokens: {token}.{next_token}")
                                    break
                            except ValueError:
                                continue
            
            # Validate the extracted GPA
            if gpa is not None:
                if 0.0 <= gpa <= 4.0:
                    response_msg = f"Got it! Your GPA is {gpa:.2f}"
                    if is_percentage and original_percentage is not None:
                        response_msg += f" (converted from {original_percentage:.1f}%)"
                    dispatcher.utter_message(text=response_msg)
                    return {"gpa": gpa}
                else:
                    dispatcher.utter_message(
                        text=f"The GPA {gpa:.2f} is outside the valid range (0.0-4.0). Please provide a valid GPA or use percentage format like '70%'."
                    )
                    return {"gpa": None}
            else:
                dispatcher.utter_message(
                    text="Please provide your GPA (0.0-4.0) or percentage (0-100%). Examples: '2.8', 'my GPA is 3.5', '70%', 'it is 75%', or 'my percentage is 85'"
                )
                return {"gpa": None}
                
        except Exception as e:
            print(f"ERROR in validate_gpa: {e}")
            dispatcher.utter_message(
                text="I encountered an error processing your GPA. Please try again with a format like '2.8' or '75%'."
            )
            return {"gpa": None}
    
    def _convert_percentage_to_gpa(self, percentage: float) -> float:
        """Convert percentage to GPA using common conversion scales"""
        if percentage < 0 or percentage > 100:
            return None
            
        # Use a common percentage to GPA conversion scale
        if percentage >= 97:
            return 4.0
        elif percentage >= 93:
            return 3.7
        elif percentage >= 90:
            return 3.3
        elif percentage >= 87:
            return 3.0
        elif percentage >= 83:
            return 2.7
        elif percentage >= 80:
            return 2.3
        elif percentage >= 77:
            return 2.0
        elif percentage >= 73:
            return 1.7
        elif percentage >= 70:
            return 1.3
        elif percentage >= 67:
            return 1.0
        elif percentage >= 65:
            return 0.7
        elif percentage >= 60:
            return 0.5
        else:
            return 0.0
    
    def _convert_gpa_to_percentage(self, gpa: float) -> float:
        """Convert GPA back to percentage for display purposes"""
        if gpa >= 4.0:
            return 97.0
        elif gpa >= 3.7:
            return 93.0
        elif gpa >= 3.3:
            return 90.0
        elif gpa >= 3.0:
            return 87.0
        elif gpa >= 2.7:
            return 83.0
        elif gpa >= 2.3:
            return 80.0
        elif gpa >= 2.0:
            return 77.0
        elif gpa >= 1.7:
            return 73.0
        elif gpa >= 1.3:
            return 70.0
        elif gpa >= 1.0:
            return 67.0
        elif gpa >= 0.7:
            return 65.0
        else:
            return 60.0

    def validate_budget(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate budget input"""
        try:
            # Handle different budget formats
            budget_str = str(slot_value).replace("£", "").replace(",", "")
            budget = float(budget_str)
            
            if budget < 5000:
                dispatcher.utter_message(
                    text="The budget seems quite low for UK universities. Most programs cost £15,000-£35,000 per year. Please double-check."
                )
            elif budget > 100000:
                dispatcher.utter_message(
                    text="That's a very high budget! You'll have many options. Let me find the best universities for you."
                )
            
            return {"budget": budget}
        except (ValueError, TypeError):
            dispatcher.utter_message(
                text="Please provide a valid budget amount in GBP (e.g., 20000 or £20,000)"
            )
            return {"budget": None}

    def validate_english_requirement_met(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate that student has some form of English proficiency proof"""
        
        # Check all English-related slots
        ielts = tracker.get_slot("ielts")
        pte = tracker.get_slot("pte")
        toefl = tracker.get_slot("toefl")
        english_waiver = tracker.get_slot("english_waiver")
        moi = tracker.get_slot("moi")

        # If any English requirement is met
        if any([ielts, pte, toefl, english_waiver, moi]):
            return {"english_requirement_met": True}
        
        # If none provided, ask for at least one
        dispatcher.utter_message(
            text="You need to provide at least one form of English proficiency: IELTS, PTE, TOEFL score, English waiver, or MOI certificate."
        )
        return {"english_requirement_met": None}

    def validate_ielts(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate IELTS score"""
        if slot_value is None:
            return {"ielts": None}
        
        try:
            ielts = float(slot_value)
            if 0.0 <= ielts <= 9.0:
                if ielts < 5.5:
                    dispatcher.utter_message(
                        text="Your IELTS score is quite low. You might need to retake the test or look for pre-sessional English courses."
                    )
                return {"ielts": ielts}
            else:
                dispatcher.utter_message(
                    text="IELTS scores range from 0.0 to 9.0. Please provide a valid score."
                )
                return {"ielts": None}
        except (ValueError, TypeError):
            dispatcher.utter_message(
                text="Please provide a valid IELTS score (e.g., 6.5)"
            )
            return {"ielts": None}

    def validate_study_level(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Normalize study level to 'ug' or 'pg'"""
        if not slot_value:
            return {"study_level": None}
        text = str(slot_value).lower()
        if any(k in text for k in ["ug", "undergrad", "bachelor", "bachelors", "undergraduate"]):
            return {"study_level": "ug"}
        if any(k in text for k in ["pg", "postgrad", "masters", "master", "postgraduate", "msc", "ma", "mba"]):
            return {"study_level": "pg"}
        dispatcher.utter_message(text="Please reply with UG (Undergraduate/Bachelors) or PG (Postgraduate/Masters).")
        return {"study_level": None}

    def validate_field_of_study(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Light normalization for field of study input."""
        if not slot_value:
            return {"field_of_study": None}
        value = str(slot_value).strip()
        if len(value) < 2:
            dispatcher.utter_message(text="Please provide a field like Computer Science, Business, Engineering, etc.")
            return {"field_of_study": None}
        return {"field_of_study": value}


class ActionWeather(Action):
    """Fetches real-time weather for UK cities"""

    def name(self) -> Text:
        return "action_weather"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # You can make this dynamic based on user input later
        location = "London,UK"
        api_key = "YOUR_OPENWEATHERMAP_API_KEY"  # Replace with your actual API key
        
        if api_key == "YOUR_OPENWEATHERMAP_API_KEY":
            dispatcher.utter_message(
                text="Weather service is currently unavailable. Generally, UK weather is mild but rainy. Pack warm clothes and a good umbrella! ☔"
            )
            return []

        url = (
            f"http://api.openweathermap.org/data/2.5/weather"
            f"?q={location}&units=metric&appid={api_key}"
        )

        try:
            resp = requests.get(url, timeout=5).json()
            temp = resp["main"]["temp"]
            desc = resp["weather"][0]["description"]
            feels_like = resp["main"]["feels_like"]
            
            dispatcher.utter_message(
                text=f"🌤️ Weather in {location.split(',')[0]}: {desc.title()}\n"
                     f"Temperature: {temp}°C (feels like {feels_like}°C)\n"
                     f"Don't forget to pack layers - UK weather can be unpredictable!"
            )
        except requests.RequestException:
            dispatcher.utter_message(
                text="Sorry, I couldn't fetch live weather data right now. UK weather is generally mild but rainy - perfect for studying indoors! 📚"
            )
        except Exception as e:
            dispatcher.utter_message(
                text="Weather service temporarily unavailable. UK weather tip: Always carry an umbrella! ☂️"
            )

        return []


class ActionLivingCost(Action):
    """Reads living-cost data from converted_checklist.json with enhanced formatting"""

    def name(self) -> Text:
        return "action_living_cost"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        try:
            path = DATA_DIR / "converted_checklist.json"
            if not path.exists():
                dispatcher.utter_message(
                    text="Living cost data is currently unavailable. Generally, budget £12,000-15,000 for London and £9,000-12,000 for other cities per year."
                )
                return []

            info = json.loads(path.read_text())
            inside = info["living_cost"]["inside_london"]
            outside = info["living_cost"]["outside_london"]

            message = (
                "💰 **UK Living Costs for Students (9 months):**\n\n"
                f"🏙️ **London:** £{inside['student_9_months_gbp']} "
                f"(~£{inside['student_monthly_gbp']}/month)\n"
                f"🌆 **Outside London:** £{outside['student_9_months_gbp']} "
                f"(~£{outside['student_monthly_gbp']}/month)\n\n"
                f"💡 **Tip:** These are official UKVI estimates. Your actual costs may vary based on lifestyle!"
            )
            
            dispatcher.utter_message(text=message)
            
        except json.JSONDecodeError:
            dispatcher.utter_message(
                text="There's an issue with the living cost data format. Please contact support."
            )
        except Exception as e:
            dispatcher.utter_message(
                text="Sorry, I couldn't load the living cost information right now. Try again later!"
            )

        return []


class ActionDocChecklist(Action):
    """Reads the document-checklist from converted_checklist.json with better formatting"""

    def name(self) -> Text:
        return "action_doc_checklist"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        try:
            path = DATA_DIR / "converted_checklist.json"
            if not path.exists():
                dispatcher.utter_message(
                    text="Document checklist is currently unavailable. Generally you need: transcripts, certificates, SOP, LOR, passport, and English test scores."
                )
                return []

            info = json.loads(path.read_text())
            checklist = info["document_checklist"]
            
            message = "📋 **UK University Application Checklist:**\n\n"
            message += "\n".join(f"✅ {item}" for item in checklist)
            message += "\n\n💡 **Tip:** Start gathering these documents early as some may take time to obtain!"
            
            dispatcher.utter_message(text=message)
            
        except json.JSONDecodeError:
            dispatcher.utter_message(
                text="There's an issue with the document checklist format. Please contact support."
            )
        except Exception as e:
            dispatcher.utter_message(
                text="Sorry, I couldn't load the document checklist right now."
            )

        return []


class ActionRecommendUniversities(Action):
    """Enhanced university recommendation with better filtering and formatting"""

    def name(self) -> Text:
        return "action_recommend_universities"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Extract slots
        gpa = tracker.get_slot("gpa")
        ielts = tracker.get_slot("ielts")
        pte = tracker.get_slot("pte")
        toefl = tracker.get_slot("toefl")
        waiver = tracker.get_slot("english_waiver")
        moi = tracker.get_slot("moi")
        budget = tracker.get_slot("budget")
        loc_pref = tracker.get_slot("location_pref")
        study_level = tracker.get_slot("study_level")
        field = tracker.get_slot("field_of_study")

        # Load normalized universities
        try:
            path = DATA_DIR / "converted_universities.json"
            if not path.exists():
                dispatcher.utter_message(
                    text="University database is currently unavailable. Please try again later or contact support."
                )
                return []
                
            data = json.loads(path.read_text())
            unis = data["universities"]
            
        except json.JSONDecodeError:
            dispatcher.utter_message(
                text="There's an issue with the university database format. Please contact support."
            )
            return []
        except Exception as e:
            dispatcher.utter_message(
                text="Sorry, I couldn't load the university data. Please try again later."
            )
            return []

        matches = []
        for uni in unis:
            if not self._meets_gpa_requirement(uni, gpa):
                continue
            if not self._meets_english_requirement(uni, ielts, pte, toefl, waiver, moi):
                continue
            if not self._meets_budget_requirement(uni, budget):
                continue
            if not self._meets_location_preference(uni, loc_pref):
                continue
            if not self._meets_study_level(uni, study_level):
                continue
            if not self._matches_field(uni, field):
                continue

            fee = self._extract_fee_from_requirements(uni)
            matches.append({
                "name": uni["name"],
                "fees": str(int(fee)) if fee else "N/A",
                "location": self._extract_location_from_name(uni["name"]) or "N/A",
                "ranking": uni.get("ranking", "N/A")
            })

        # Sort by fees (ascending)
        matches.sort(key=lambda x: float(x["fees"]) if x["fees"] != "N/A" else float('inf'))

        if matches:
            if len(matches) > 10:
                matches = matches[:10]  # Limit to top 10
                
            message = f"🎓 **Found {len(matches)} universities matching your profile:**\n\n"
            
            for i, uni in enumerate(matches, 1):
                fees_str = f"£{uni['fees']}" if uni['fees'] != "N/A" else "Contact university"
                message += f"{i}. **{uni['name']}**\n"
                message += f"   💰 Fees: {fees_str}\n"
                message += f"   📍 Location: {uni['location']}\n\n"
            
            message += "💡 **Next Steps:** Research these universities, check specific course requirements, and start your applications!"
            
        else:
            message = (
                "😔 Sorry, I couldn't find universities matching all your criteria.\n\n"
                "**Suggestions:**\n"
                "• Consider retaking English tests for higher scores\n"
                "• Look into foundation programs\n"
                "• Increase your budget range\n"
                "• Consider different locations\n\n"
                "Would you like me to show universities with slightly relaxed criteria?"
            )

        dispatcher.utter_message(text=message)
        return []

    def _meets_gpa_requirement(self, uni: Dict, gpa: float) -> bool:
        """Check if GPA meets university requirement"""
        if gpa is None:
            return False
            
        reqs = uni.get("requirements", {})
        ug = reqs.get("undergraduate", "")
        
        try:
            # Extract minimum GPA from requirements string
            if "GPA" in ug:
                min_gpa = float(ug.split("GPA")[1].split()[0])
                return gpa >= min_gpa
        except (IndexError, ValueError):
            pass
        
        # Default minimum GPA if not specified
        return gpa >= 2.5

    def _meets_english_requirement(self, uni: Dict, ielts: float, pte: float, 
                                 toefl: float, waiver: bool, moi: bool) -> bool:
        """Check if any English requirement is met"""
        if waiver or moi:
            return True
            
        reqs = uni.get("requirements", {})
        ug = reqs.get("undergraduate", "")
        
        # Check IELTS
        if ielts and "IELTS" in ug:
            try:
                min_ielts = float(ug.split("IELTS")[1].split()[0])
                if ielts >= min_ielts:
                    return True
            except (IndexError, ValueError):
                pass
        
        # Check PTE
        if pte and "PTE" in ug:
            try:
                min_pte = float(ug.split("PTE")[1].split()[0])
                if pte >= min_pte:
                    return True
            except (IndexError, ValueError):
                pass
        
        # Check TOEFL
        if toefl and "TOEFL" in ug:
            try:
                min_toefl = float(ug.split("TOEFL")[1].split()[0])
                if toefl >= min_toefl:
                    return True
            except (IndexError, ValueError):
                pass
        
        # Default: if no English scores provided, assume they'll handle it later
        # Don't block users without English scores - they might be working on it
        return True

    def _meets_budget_requirement(self, uni: Dict, budget: float) -> bool:
        """Check if budget meets university fees"""
        if budget is None:
            return True  # No budget constraint
            
        # Use the new fee extraction method
        fee = self._extract_fee_from_requirements(uni)
        if fee:
            return budget >= fee
        
        return True  # If fee not specified, assume it fits

    def _extract_location_from_name(self, name: str) -> str:
        """Extract location from university name"""
        if not name:
            return ""
            
        # Look for location patterns
        import re
        
        # Pattern: "Location: ..." 
        location_match = re.search(r'Location:\s*([^\n]+)', name)
        if location_match:
            location = location_match.group(1).strip()
            # Clean up common suffixes
            location = re.sub(r',\s*United Kingdom.*$', '', location)
            location = re.sub(r',\s*UK.*$', '', location)
            return location
        
        # Look for city names in the text
        cities = ["London", "Manchester", "Birmingham", "Liverpool", "Leeds", "Sheffield", 
                  "Bristol", "Nottingham", "Southampton", "Portsmouth", "Brighton", 
                  "Leicester", "Coventry", "Derby", "Huddersfield", "Greenwich", 
                  "Hertfordshire", "Hatfield", "Kent", "Essex"]
        
        for city in cities:
            if city in name:
                return city
                
        return ""

    def _extract_fee_from_requirements(self, uni: Dict) -> float:
        """Extract fee from requirements text"""
        reqs = uni.get("requirements", {})
        text = reqs.get("postgraduate", "") or reqs.get("undergraduate", "")
        
        if not text or text in ["nan", "", "NaN"]:
            return None
            
        # Look for fee patterns in the text
        import re
        
        # Pattern 1: "Fee: 17250" or "Fee:17250"
        fee_match = re.search(r'Fee:?\s*(\d+)', text, re.IGNORECASE)
        if fee_match:
            return float(fee_match.group(1))
        
        # Pattern 2: "17250 GBP" or "£17250"
        gbp_match = re.search(r'[£]?(\d+)\s*(?:GBP|gbp)', text, re.IGNORECASE)
        if gbp_match:
            return float(gbp_match.group(1))
        
        # Pattern 3: Numbers that look like fees (15000-50000 range)
        number_matches = re.findall(r'\b(\d{5,6})\b', text)
        for num in number_matches:
            fee = float(num)
            if 10000 <= fee <= 50000:  # Reasonable fee range
                return fee
        
        return None

    def _meets_location_preference(self, uni: Dict, loc_pref: str) -> bool:
        """Check if university location matches preference"""
        if not loc_pref:
            return True  # No location preference
        
        uni_name = uni.get("name", "").lower()
        uni_location = uni.get("location", "").lower()
        loc_pref_lower = loc_pref.lower()
        
        # Check for specific location mentions
        if "london" in loc_pref_lower:
            return "london" in uni_name or "london" in uni_location
        elif "outside london" in loc_pref_lower:
            return "london" not in uni_name and "london" not in uni_location
        else:
            # Check if preference matches city/location
            return loc_pref_lower in uni_name or loc_pref_lower in uni_location

    def _meets_study_level(self, uni: Dict, study_level: str) -> bool:
        if not study_level:
            return True
        # Dataset is program-agnostic; assume both unless explicitly mentioned in text
        text = (uni.get("requirements", {}).get("postgraduate") or "") + "\n" + (uni.get("requirements", {}).get("undergraduate") or "")
        if study_level == "pg":
            return "postgraduate" in text.lower() or True
        if study_level == "ug":
            return "undergraduate" in text.lower() or True
        return True

    def _matches_field(self, uni: Dict, field: str) -> bool:
        if not field:
            return True
        name = (uni.get("name") or "").lower()
        text = (uni.get("requirements", {}).get("postgraduate") or "") + "\n" + (uni.get("requirements", {}).get("undergraduate") or "")
        field_l = field.lower()
        return field_l in name or field_l in text


class ActionRecommendUniversitiesRelaxed(Action):
    """Show universities with relaxed criteria when strict matching fails"""

    def name(self) -> Text:
        return "action_recommend_universities_relaxed"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Extract available information
        gpa = tracker.get_slot("gpa")
        budget = tracker.get_slot("budget")
        loc_pref = tracker.get_slot("location_pref")

        # Load universities
        try:
            path = DATA_DIR / "converted_universities.json"
            if not path.exists():
                dispatcher.utter_message(text="University database is currently unavailable.")
                return []
                
            data = json.loads(path.read_text())
            unis = data["universities"]
            
        except Exception:
            dispatcher.utter_message(text="Sorry, I couldn't load the university data.")
            return []

        # Very relaxed matching - only check budget and basic GPA
        matches = []
        for uni in unis:
            # Very lenient GPA check (2.0+ or not specified)
            if gpa and gpa < 2.0:
                continue
                
            # Relaxed budget check (allow 10% over budget)
            if budget:
                fee = self._extract_fee_from_requirements(uni)
                if fee and fee > budget * 1.1:  # Allow 10% over
                    continue

            fee = self._extract_fee_from_requirements(uni)
            matches.append({
                "name": uni["name"],
                "fees": str(int(fee)) if fee else "N/A",
                "location": self._extract_location_from_name(uni["name"]) or "N/A",
                "ranking": uni.get("ranking", "N/A"),
                "note": self._get_relaxed_note(uni, gpa, budget)
            })

        # Sort by fees and limit to 15
        matches.sort(key=lambda x: float(x["fees"]) if x["fees"] != "N/A" else float('inf'))
        matches = matches[:15]

        if matches:
            message = f"🎓 **Found {len(matches)} universities with relaxed criteria:**\n\n"
            message += "💡 *Note: Some may require foundation programs or English test improvements*\n\n"
            
            for i, uni in enumerate(matches, 1):
                fees_str = f"£{uni['fees']}" if uni['fees'] != "N/A" else "Contact university"
                message += f"{i}. **{uni['name']}**\n"
                message += f"   💰 Fees: {fees_str}\n"
                message += f"   📍 Location: {uni['location']}\n"
                if uni['note']:
                    message += f"   📝 Note: {uni['note']}\n"
                message += "\n"
            
            message += "🎯 **Next Steps:**\n"
            message += "• Research specific course requirements\n"
            message += "• Consider foundation programs if needed\n"
            message += "• Improve English scores if required\n"
            message += "• Contact universities directly for guidance"
            
        else:
            message = "😔 Even with relaxed criteria, I couldn't find suitable matches. Consider foundation programs or contact universities directly for guidance."

        dispatcher.utter_message(text=message)
        return []

    def _get_relaxed_note(self, uni: Dict, gpa: float, budget: float) -> str:
        """Generate helpful notes for relaxed matches"""
        notes = []
        
        # Check if might need foundation program
        reqs = uni.get("requirements", {}).get("undergraduate", "")
        if gpa and "GPA" in reqs:
            try:
                min_gpa = float(reqs.split("GPA")[1].split()[0])
                if gpa < min_gpa:
                    notes.append("May need foundation program")
            except (IndexError, ValueError):
                pass
                
        # Check if over budget
        if budget:
            fee = self._extract_fee_from_requirements(uni)
            if fee and fee > budget:
                over_by = fee - budget
                notes.append(f"£{over_by:.0f} over budget")
        
        return ", ".join(notes)

    def _extract_fee_from_requirements(self, uni: Dict) -> float:
        """Extract fee from requirements text"""
        reqs = uni.get("requirements", {})
        text = reqs.get("postgraduate", "") or reqs.get("undergraduate", "")
        
        if not text or text in ["nan", "", "NaN"]:
            return None
            
        # Look for fee patterns in the text
        import re
        
        # Pattern 1: "Fee: 17250" or "Fee:17250"
        fee_match = re.search(r'Fee:?\s*(\d+)', text, re.IGNORECASE)
        if fee_match:
            return float(fee_match.group(1))
        
        # Pattern 2: "17250 GBP" or "£17250"
        gbp_match = re.search(r'[£]?(\d+)\s*(?:GBP|gbp)', text, re.IGNORECASE)
        if gbp_match:
            return float(gbp_match.group(1))
        
        # Pattern 3: Numbers that look like fees (15000-50000 range)
        number_matches = re.findall(r'\b(\d{5,6})\b', text)
        for num in number_matches:
            fee = float(num)
            if 10000 <= fee <= 50000:  # Reasonable fee range
                return fee
        
        return None

    def _extract_location_from_name(self, name: str) -> str:
        """Extract location from university name"""
        if not name:
            return ""
            
        # Look for location patterns
        import re
        
        # Pattern: "Location: ..." 
        location_match = re.search(r'Location:\s*([^\n]+)', name)
        if location_match:
            location = location_match.group(1).strip()
            # Clean up common suffixes
            location = re.sub(r',\s*United Kingdom.*$', '', location)
            location = re.sub(r',\s*UK.*$', '', location)
            return location
        
        # Look for city names in the text
        cities = ["London", "Manchester", "Birmingham", "Liverpool", "Leeds", "Sheffield", 
                  "Bristol", "Nottingham", "Southampton", "Portsmouth", "Brighton", 
                  "Leicester", "Coventry", "Derby", "Huddersfield", "Greenwich", 
                  "Hertfordshire", "Hatfield", "Kent", "Essex"]
        
        for city in cities:
            if city in name:
                return city
                
        return ""


class ActionSafetySelfHarm(Action):
    """Provide empathetic, crisis-safe response with resources. No instructions or judgment."""

    def name(self) -> Text:
        return "action_safety_self_harm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        message = (
            "I'm really sorry you're feeling this way. You deserve support and you don't have to go through this alone.\n\n"
            "If you're in immediate danger, please call your local emergency number right now.\n\n"
            "You can talk to someone confidentially: \n"
            "• In Nepal: TUTH Suicide Hotline +977-9840021600 (hours vary)\n"
            "• International: Befrienders Worldwide (list of helplines): https://www.befrienders.org/\n"
            "• If you're in the UK: Samaritans 116 123 (free, 24/7)\n\n"
            "If you'd like, I can stay here and listen. Would you like to talk about what you're going through?"
        )
        dispatcher.utter_message(text=message)
        return []


class ActionSafetyIllegalDanger(Action):
    """Refuse illegal/dangerous requests and redirect to lawful, safe alternatives."""

    def name(self) -> Text:
        return "action_safety_illegal_danger"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        message = (
            "I can't assist with illegal or dangerous activities. If you had safety concerns or legal questions, I can help with lawful, responsible information—"
            "for example UK study options, visas, campus safety, or student support services. How can I help you safely?"
        )
        dispatcher.utter_message(text=message)
        return []


# Improve ChatGPT fallback to attempt reclassification/answering with safety
class ActionChatGPTFallback(Action):
    """ChatGPT fallback for handling unpredictable user inputs with context awareness and safety."""

    def name(self) -> Text:
        return "action_chatgpt_fallback"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            dispatcher.utter_message(
                text=(
                    "I'm not sure I understood that completely. Here's what I can help you with:\n\n"
                    "🎓 University recommendations\n📋 Application/visa guidance\n💰 Living costs & scholarships\n\n"
                    "Could you rephrase your question about UK study?"
                )
            )
            return []

        try:
            user_message = tracker.latest_message.get('text', '')
            system_prompt = (
                "You are a helpful, safety-aware assistant for UK study guidance."
                "- Be concise and practical."
                "- If user indicates self-harm or suicidal ideation, respond with crisis-safe guidance and helplines; do not provide analysis beyond support."
                "- If user asks for illegal/dangerous help (weapons, hacking, fake docs), refuse and redirect to safe, legal alternatives."
                "- Otherwise, answer about UK study, visas, costs, scholarships, and universities using general knowledge."
                "- Prefer structured bullets for clarity."
            )
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=400,
                temperature=0.4,
            )
            answer = response.choices[0].message.content.strip()
            dispatcher.utter_message(text=answer)
            return []
        except Exception:
            dispatcher.utter_message(
                text="I'm having trouble understanding that right now. Could you rephrase your question about UK universities?"
            )
            return []


class ActionVisaInfo(Action):
    """Provides UK student visa information"""

    def name(self) -> Text:
        return "action_visa_info"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        message = (
            "🛂 **UK Student Visa (Student Route) Requirements:**\n\n"
            "📋 **Essential Documents:**\n"
            "• Valid passport\n"
            "• CAS (Confirmation of Acceptance for Studies) from university\n"
            "• Financial proof: Tuition fees + £1,334/month living costs\n"
            "• English proficiency proof (IELTS/PTE/TOEFL)\n"
            "• TB test results (required for Nepal)\n"
            "• Academic transcripts and certificates\n\n"
            "💰 **Visa Fees:** £363 + £470/year health surcharge\n\n"
            "⏰ **Timeline:** Apply 3 months before course starts\n\n"
            "📍 **Application:** Online at gov.uk, biometrics at VFS Global Kathmandu\n\n"
            "💡 **Tip:** Start visa application immediately after receiving CAS!"
        )
        
        dispatcher.utter_message(text=message)
        return []


class ActionScholarshipInfo(Action):
    """Provides scholarship information for Nepali students"""

    def name(self) -> Text:
        return "action_scholarship_info"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        message = (
            "🎓 **Scholarships for Nepali Students in UK:**\n\n"
            "🏆 **Government Scholarships:**\n"
            "• Chevening Scholarships (full funding)\n"
            "• Commonwealth Scholarships (full funding)\n"
            "• GREAT Scholarships (£10,000)\n\n"
            "🏫 **University Scholarships:**\n"
            "• Merit-based: Up to 50% tuition reduction\n"
            "• Vice-Chancellor awards\n"
            "• International student bursaries\n"
            "• Subject-specific scholarships\n\n"
            "💡 **Application Tips:**\n"
            "• Apply early (many have December/January deadlines)\n"
            "• Strong academic record required\n"
            "• Compelling personal statement essential\n"
            "• Leadership/community service helps\n\n"
            "🔗 **Research:** Check individual university websites for specific opportunities!"
        )
        
        dispatcher.utter_message(text=message)
        return []


class ActionUniversityRanking(Action):
    """Provides information about UK university rankings"""

    def name(self) -> Text:
        return "action_university_ranking"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        message = (
            "📊 **UK University Rankings Guide:**\n\n"
            "🏆 **Top Ranking Systems:**\n"
            "• QS World University Rankings\n"
            "• Times Higher Education (THE)\n"
            "• Complete University Guide (UK specific)\n"
            "• Guardian University Guide\n\n"
            "🎯 **What to Consider:**\n"
            "• Overall ranking vs subject ranking\n"
            "• Graduate employability rates\n"
            "• Student satisfaction scores\n"
            "• Research quality (REF ratings)\n\n"
            "💡 **For Nepali Students:**\n"
            "• Russell Group universities are highly regarded\n"
            "• Consider post-study work opportunities\n"
            "• Location and living costs matter\n"
            "• Industry connections and placement rates\n\n"
            "Would you like recommendations based on your field of study?"
        )
        
        dispatcher.utter_message(text=message)
        return []


class ActionApplicationDeadline(Action):
    """Provides information about UK university application deadlines"""

    def name(self) -> Text:
        return "action_application_deadline"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        message = (
            "📅 **UK University Application Deadlines:**\n\n"
            "🍂 **September/October Intake:**\n"
            "• Applications open: September previous year\n"
            "• Early deadline: January 15 (Oxford/Cambridge/Medicine)\n"
            "• Main deadline: June 30\n"
            "• Late applications: Until September (if places available)\n\n"
            "❄️ **January/February Intake:**\n"
            "• Applications: September - November\n"
            "• Limited courses available\n"
            "• Mainly postgraduate programs\n\n"
            "⚡ **Important Notes:**\n"
            "• Popular universities fill up quickly\n"
            "• Apply early for better scholarship chances\n"
            "• UCAS deadline for undergrad: January 26\n"
            "• Direct applications vary by university\n\n"
            "🎯 **Tip:** Don't wait for deadlines - apply as soon as your documents are ready!"
        )
        
        dispatcher.utter_message(text=message)
        return []


class ActionCompareUniversities(Action):
    """Helps compare universities based on various factors"""

    def name(self) -> Text:
        return "action_compare_universities"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        message = (
            "⚖️ **University Comparison Factors:**\n\n"
            "🎓 **Academic Excellence:**\n"
            "• Rankings in your subject area\n"
            "• Research quality and facilities\n"
            "• Faculty reputation\n"
            "• Course content and structure\n\n"
            "💰 **Financial Considerations:**\n"
            "• Tuition fees\n"
            "• Living costs by location\n"
            "• Scholarship availability\n"
            "• Part-time work opportunities\n\n"
            "🌟 **Student Experience:**\n"
            "• Campus facilities\n"
            "• International student support\n"
            "• Student satisfaction ratings\n"
            "• Extracurricular activities\n\n"
            "🚀 **Career Prospects:**\n"
            "• Graduate employment rates\n"
            "• Industry connections\n"
            "• Alumni network\n"
            "• Location for job opportunities\n\n"
            "Tell me which specific universities you'd like to compare!"
        )
        
        dispatcher.utter_message(text=message)
        return []


class ActionFieldSpecific(Action):
    """Handles field-specific university recommendations"""

    def name(self) -> Text:
        return "action_field_specific"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Get the user's message to extract the field
        user_message = tracker.latest_message.get('text', '').lower()
        
        # Extract field of study
        field = self._extract_field(user_message)
        
        message = (
            f"🎯 **Field-Specific Guidance: {field}**\n\n"
            "Great! I understand you're interested in this field. To provide the best university recommendations, "
            "I need to know more about your academic profile.\n\n"
            "📋 **Please provide:**\n"
            "• Your GPA/CGPA\n"
            "• English test scores (IELTS/PTE/TOEFL) or English waiver\n"
            "• Your budget range\n"
            "• Location preference (London/Outside London)\n\n"
            "💡 **Example:**\n"
            f"\"My GPA is 3.4, IELTS 6.5, budget £20000, prefer outside London for {field}\"\n\n"
            "This will help me find the best universities for your specific field and profile!"
        )
        
        dispatcher.utter_message(text=message)
        return []

    def _extract_field(self, message: str) -> str:
        """Extract field of study from user message"""
        
        field_mapping = {
            'it': 'Information Technology',
            'computer science': 'Computer Science',
            'engineering': 'Engineering',
            'business': 'Business',
            'medicine': 'Medicine',
            'law': 'Law',
            'psychology': 'Psychology',
            'economics': 'Economics',
            'mba': 'MBA',
            'data science': 'Data Science',
            'mechanical': 'Mechanical Engineering',
            'civil': 'Civil Engineering',
            'electrical': 'Electrical Engineering',
            'software': 'Software Engineering',
            'finance': 'Finance',
            'accounting': 'Accounting',
            'marketing': 'Marketing',
            'management': 'Management',
            'biotechnology': 'Biotechnology',
            'chemistry': 'Chemistry',
            'physics': 'Physics',
            'mathematics': 'Mathematics',
            'architecture': 'Architecture',
            'design': 'Design',
            'media': 'Media Studies',
            'journalism': 'Journalism',
            'education': 'Education',
            'nursing': 'Nursing',
            'pharmacy': 'Pharmacy'
        }
        
        for key, value in field_mapping.items():
            if key in message:
                return value
        
        return "your chosen field"


class ActionUniversitiesByBudget(Action):
    """Handle direct budget-based university queries without requiring full profile"""
    
    def name(self) -> Text:
        return "action_universities_by_budget"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        # Extract budget from the message
        budget = tracker.get_slot("budget")
        
        if not budget:
            dispatcher.utter_message(
                text="I didn't catch your budget amount. Could you please specify your budget? For example: 'Show me universities under £20,000'"
            )
            return []
        
        try:
            budget = float(budget)
        except (ValueError, TypeError):
            dispatcher.utter_message(
                text="Please provide a valid budget amount in GBP (e.g., 20000 or £20,000)"
            )
            return []
        
        # Load university data
        try:
            path = DATA_DIR / "converted_universities.json"
            if not path.exists():
                dispatcher.utter_message(
                    text="University database is currently unavailable. Please try again later."
                )
                return []
                
            data = json.loads(path.read_text())
            unis = data["universities"]
            
        except Exception as e:
            dispatcher.utter_message(
                text="Sorry, I couldn't load the university data. Please try again later."
            )
            return []
        
        # Find universities within budget
        matches = []
        for uni in unis:
            if uni.get("name") in [None, "NaN", "", "nan"]:
                continue
                
            fee = self._extract_fee_from_requirements(uni)
            if fee and fee <= budget:
                matches.append({
                    "name": uni["name"],
                    "fee": fee,
                    "requirements": uni.get("requirements", {}).get("postgraduate", "")
                })
        
        # Sort by fee (ascending)
        matches.sort(key=lambda x: x["fee"])
        
        if matches:
            # Limit to top 10 results
            matches = matches[:10]
            
            message = f"💰 **Found {len(matches)} universities within your £{budget:,.0f} budget:**\n\n"
            
            for i, uni in enumerate(matches, 1):
                # Clean up university name
                name_parts = uni["name"].split("\n")[0].strip()
                message += f"{i}. **{name_parts}**\n"
                message += f"   💰 Fee: £{uni['fee']:,.0f}\n"
                
                # Extract location if available
                location = self._extract_location_from_name(uni["name"])
                if location:
                    message += f"   📍 Location: {location}\n"
                    
                message += "\n"
            
            message += f"\n💡 **Next Steps:**\n"
            message += f"• Research these universities in detail\n"
            message += f"• Check specific course requirements\n"
            message += f"• Verify current fees on university websites\n"
            message += f"• Consider additional costs (living expenses, visa, etc.)\n\n"
            message += f"Would you like me to help you with anything else, such as admission requirements or application process?"
            
        else:
            message = f"😔 **No universities found within £{budget:,.0f} budget.**\n\n"
            message += f"💡 **Suggestions:**\n"
            message += f"• Most UK universities charge £15,000-£35,000 per year\n"
            message += f"• Consider universities outside London (generally cheaper)\n"
            message += f"• Look into scholarships and financial aid\n"
            message += f"• Check for universities with payment plans\n\n"
            message += f"Would you like me to show universities with a higher budget range?"
        
        dispatcher.utter_message(text=message)
        return []
    
    def _extract_fee_from_requirements(self, uni: Dict) -> float:
        """Extract fee from requirements text"""
        reqs = uni.get("requirements", {})
        text = reqs.get("postgraduate", "") or reqs.get("undergraduate", "")
        
        if not text or text in ["nan", "", "NaN"]:
            return None
            
        # Look for fee patterns in the text
        import re
        
        # Pattern 1: "Fee: 17250" or "Fee:17250"
        fee_match = re.search(r'Fee:?\s*(\d+)', text, re.IGNORECASE)
        if fee_match:
            return float(fee_match.group(1))
        
        # Pattern 2: "17250 GBP" or "£17250"
        gbp_match = re.search(r'[£]?(\d+)\s*(?:GBP|gbp)', text, re.IGNORECASE)
        if gbp_match:
            return float(gbp_match.group(1))
        
        # Pattern 3: Numbers that look like fees (15000-50000 range)
        number_matches = re.findall(r'\b(\d{5,6})\b', text)
        for num in number_matches:
            fee = float(num)
            if 10000 <= fee <= 50000:  # Reasonable fee range
                return fee
        
        return None
    
    def _extract_location_from_name(self, name: str) -> str:
        """Extract location from university name"""
        if not name:
            return ""
            
        # Look for location patterns
        import re
        
        # Pattern: "Location: ..." 
        location_match = re.search(r'Location:\s*([^\n]+)', name)
        if location_match:
            location = location_match.group(1).strip()
            # Clean up common suffixes
            location = re.sub(r',\s*United Kingdom.*$', '', location)
            location = re.sub(r',\s*UK.*$', '', location)
            return location
        
        # Look for city names in the text
        cities = ["London", "Manchester", "Birmingham", "Liverpool", "Leeds", "Sheffield", 
                  "Bristol", "Nottingham", "Southampton", "Portsmouth", "Brighton", 
                  "Leicester", "Coventry", "Derby", "Huddersfield", "Greenwich", 
                  "Hertfordshire", "Hatfield", "Kent", "Essex"]
        
        for city in cities:
            if city in name:
                return city
                
        return ""


class ActionIELTSWaiverUniversities(Action):
    """List universities that mention IELTS waiver/MOI acceptance in requirements"""

    def name(self) -> Text:
        return "action_ielts_waiver_universities"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        try:
            path = DATA_DIR / "converted_universities.json"
            if not path.exists():
                dispatcher.utter_message(text="University database is currently unavailable.")
                return []
            data = json.loads(path.read_text())
            unis = data["universities"]
        except Exception:
            dispatcher.utter_message(text="Sorry, I couldn't load the university data.")
            return []

        keywords = [
            "waiver", "english waiver", "moi", "medium of instruction", "duolingo", "oxford test",
            "IELTS waiver", "Apply without IELTS", "LanguageCert", "university test", "Oxford  Test"
        ]
        matches: List[Dict[str, Any]] = []
        for uni in unis:
            req = (uni.get("requirements", {}).get("postgraduate") or "") + "\n" + (uni.get("requirements", {}).get("undergraduate") or "")
            lower = req.lower()
            if any(k.lower() in lower for k in keywords):
                fee = ActionRecommendUniversities(None)._extract_fee_from_requirements(uni) if hasattr(ActionRecommendUniversities, "_extract_fee_from_requirements") else None
                matches.append({
                    "name": uni.get("name", "Unknown").split("\n")[0].strip(),
                    "fee": fee
                })

        # Prefer London/outside diverse list; sort by fee if available
        matches.sort(key=lambda x: (float(x["fee"]) if x["fee"] else 1e9, x["name"]))
        matches = matches[:10] if matches else []

        if not matches:
            dispatcher.utter_message(text="I couldn't find explicit IELTS-waiver mentions in the data. Many universities accept MOI/waiver depending on profile. Consider Middlesex, Coventry, UEL, UWS, Bedfordshire, Hertfordshire.")
            return []

        msg = "✅ Universities mentioning IELTS waiver/MOI acceptance:\n\n"
        for i, m in enumerate(matches, 1):
            fee_str = f"£{int(m['fee']):,}" if m["fee"] else "Check prospectus"
            msg += f"{i}. {m['name']} — Approx fee: {fee_str}\n"
        msg += "\nTip: Waiver policies vary by course and profile (grade 12 English, MOI, or university tests). Always verify on the course page."
        dispatcher.utter_message(text=msg)
        return []


class ActionAffordableUniversities(Action):
    """List most affordable universities by scanning fees in the dataset"""

    def name(self) -> Text:
        return "action_affordable_universities"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        try:
            path = DATA_DIR / "converted_universities.json"
            if not path.exists():
                dispatcher.utter_message(text="University database is currently unavailable.")
                return []
            data = json.loads(path.read_text())
            unis = data["universities"]
        except Exception:
            dispatcher.utter_message(text="Sorry, I couldn't load the university data.")
            return []

        affordable: List[Dict[str, Any]] = []
        helper = ActionRecommendUniversities(None)
        for uni in unis:
            fee = helper._extract_fee_from_requirements(uni)
            if fee:
                affordable.append({"name": uni.get("name", "Unknown").split("\n")[0].strip(), "fee": fee})

        affordable.sort(key=lambda x: x["fee"])
        top = affordable[:10]

        if not top:
            dispatcher.utter_message(text="Fee information is sparse in the dataset. However, universities like Bedfordshire, Teesside, Ulster (Birmingham), UWS, and York St John often have comparatively lower fees. Please check their official pages for exact amounts.")
            return []

        msg = "💸 Most affordable options in our dataset (indicative annual tuition):\n\n"
        for i, uni in enumerate(top, 1):
            msg += f"{i}. {uni['name']} — £{uni['fee']:,.0f}\n"
        msg += "\nNote: Fees vary by course and intake. Always verify the latest fees on the university website."
        dispatcher.utter_message(text=msg)
        return []