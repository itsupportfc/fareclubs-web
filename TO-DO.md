# Application level changes
1. setup dockerfile and docker compose to run my backend on docker
2. use redis instead of simple python storage for cache currently


# FareQuote response check 

1. "IsPanRequiredAtTicket" or "IsPanRequiredAtBook" is true: then take PAN input in the booking page
2. "IsPassportRequiredAtTicket" or "IsPassportRequiredAtBook" is true: 
    a. then take PASSPORT input in the booking page
    b. check for these nodes also
      i. "**IsPassportFullDetailRequiredAtBook**":true => then ask for these inputs
          "PassportNo":"Z4337010",
          "PassportExpiry":"2028-01-15T00:00:00",
          "PassportIssueDate":"2022-04-18T00:00:00",
          "PassportIssueCountryCode":"IN"
      ii. "**IsPassportFullDetailRequiredAtBook**":false => then ask for these inputs
          "PassportNo":"Z4337010",
          "PassportExpiry":"2028-01-15T00:00:00",
3. **IsGSTMandatory**: 
    a. then ask for these inputs on the booking page
    b.then in the lead passenger object pass these: 
        "IsLeadPax": true,        
        "GSTCompanyAddress": "tek travel, gurugram",
        "GSTCompanyContactNumber": "9874563102",
        "GSTCompanyName": "Tek Travel",
        "GSTNumber": "18AABCT3518Q1ZV",
        "GSTCompanyEmail": "test@api.in"
        

6. IsPriceChanged or IsTimeChanged == tru => then ask the user again
8. FlightDetailChangeInfo





# pricing concept change to be made

    1. Base fare and tax from fare breakdown array(FareQuote response) should be divided by pax count and then pass in ticket or book request. For example if Base Fare received is 1000 and passenger count is 2 then divide 1000 by 2 and then pass 500 for each passenger in ticket request same process need to be followed for the Tax node.

    example in Fare quote response:   
    
        "FareBreakdown": [
                    {
                        "Currency": "INR",
                        "PassengerType": 1,  // adult
                        "PassengerCount": 2,
                        "BaseFare": 12000, 
                        "Tax": 2488,
                        "YQTax": 0,
                        "AdditionalTxnFeeOfrd": 0,
                        "AdditionalTxnFeePub": 0,
                        "PGCharge": 0
                    },
                    {
                        "Currency": "INR",
                        "PassengerType": 2, // child
                        "PassengerCount": 2,
                        "BaseFare": 12000,
                        "Tax": 2488,
                        "YQTax": 0,
                        "AdditionalTxnFeeOfrd": 0,
                        "AdditionalTxnFeePub": 0,
                        "PGCharge": 0
                    },
                    {
                        "Currency": "INR",
                        "PassengerType": 3, // infant
                        "PassengerCount": 1,
                        "BaseFare": 2500,
                        "Tax": 482,
                        "YQTax": 0,
                        "AdditionalTxnFeeOfrd": 0,
                        "AdditionalTxnFeePub": 0,
                        "PGCharge": 0
                    }
                ], 
    

    then for each passenger, pass the fare like this in book and ticker api passengers array:


        "Passengers": [
      {
        "Title": "Mr",
        "FirstName": "ashish",
        "LastName": "ashu",
        "PaxType": 1,
        "DateOfBirth": "1995-02-06T00:00:00",
        "Gender": 1,
        "PassportNo": "KJHHJKHKJH",
        "PassportExpiry": "2025-02-06T00:00:00",
        "AddressLine1": "123, Test",
        "AddressLine2": "",
        "Fare": {
          "Currency": "INR",
          "BaseFare": 6000,
                      "Tax": 1244,
                      "YQTax": 0,
                      "AdditionalTxnFeeOfrd": 0,
                      "AdditionalTxnFeePub": 0,
                      "PGCharge": 0,
          "OtherCharges": 944.00,
          "Discount": 0,
                  "PublishedFare": 32902,
                  "CommissionEarned": 0,
                  "PLBEarned": 0,
                  "IncentiveEarned": 0,
                  "OfferedFare": 32902.00,
                  "TdsOnCommission": 0,
                  "TdsOnPLB": 0,
                  "TdsOnIncentive": 0,
                  "ServiceFee": 0
        },
        "Meal": {
          "Code": "AVML",
          "Description": "Vegetarian Hindu"
        },
        "SeatPreference": {
          "Code": "W",
          "Description": "Window"
        },
        "City": "Gurgaon",
        "CountryCode": "IN",
        "CountryName": "India",
        "Nationality": "IN",
        "ContactNo": "9879879877",
        "Email": "harsh@tbtq.in",
        "IsLeadPax": true,
        "FFAirlineCode": null,
        "FFNumber": "",
        "GSTCompanyAddress": "",
        "GSTCompanyContactNumber": "",
        "GSTCompanyName": "",
        "GSTNumber": "",
        "GSTCompanyEmail": ""
      },
      {
        "Title": "Mr",
        "FirstName": "udham",
        "LastName": "rathore",
        "PaxType": 1,
        "DateOfBirth": "1997-10-06T00:00:00",
        "Gender": 1,
        "PassportNo": "KJHHJKHKJH",
        "PassportExpiry": "2025-12-06T00:00:00",
        "AddressLine1": "123, Test",
        "AddressLine2": "",
        "Fare": {
                 "Currency": "INR",
          "BaseFare": 6000,
                      "Tax": 1244,
                      "YQTax": 0,
                      "AdditionalTxnFeeOfrd": 0,
                      "AdditionalTxnFeePub": 0,
                      "PGCharge": 0,
          "OtherCharges": 944.00,
          "Discount": 0,
                  "PublishedFare": 32902,
                  "CommissionEarned": 0,
                  "PLBEarned": 0,
                  "IncentiveEarned": 0,
                  "OfferedFare": 32902.00,
                  "TdsOnCommission": 0,
                  "TdsOnPLB": 0,
                  "TdsOnIncentive": 0,
                  "ServiceFee": 0
        },
        "Meal": {
          "Code": "AVML",
          "Description": "Vegetarian Hindu"
        },
        "SeatPreference": {
          "Code": "W",
          "Description": "Window"
        },
        "City": "Gurgaon",
        "CountryCode": "IN",
        "CountryName": "India",
        "Nationality": "IN",
        "ContactNo": "9879879877",
        "Email": "harsh@tbtq.in",
        "IsLeadPax": false,
        "FFAirlineCode": null,
        "FFNumber": "",
        "GSTCompanyAddress": "",
        "GSTCompanyContactNumber": "",
        "GSTCompanyName": "",
        "GSTNumber": "",
        "GSTCompanyEmail": ""
      },
      {
        "Title": "Mr",
        "FirstName": "vishal",
        "LastName": "gupta",
        "PaxType": 2,
        "DateOfBirth": "2012-12-09T00:00:00",
        "Gender": 1,
        "PassportNo": "KJHHJKHKJH",
        "PassportExpiry": "2022-02-06T00:00:00",
        "AddressLine1": "123, Test",
        "AddressLine2": "",
        "Fare": {
                  "Currency": "INR",
          "BaseFare": 6000,
                      "Tax": 1244,
                      "YQTax": 0,
                      "AdditionalTxnFeeOfrd": 0,
                      "AdditionalTxnFeePub": 0,
                      "PGCharge": 0,
          "OtherCharges": 944.00,
          "Discount": 0,
                  "PublishedFare": 32902,
                  "CommissionEarned": 0,
                  "PLBEarned": 0,
                  "IncentiveEarned": 0,
                  "OfferedFare": 32902.00,
                  "TdsOnCommission": 0,
                  "TdsOnPLB": 0,
                  "TdsOnIncentive": 0,
                  "ServiceFee": 0
        },
        "Meal": {
          "Code": "CHML",
          "Description": "Child Food"
        },
        "SeatPreference": {
          "Code": "A",
          "Description": "Aisle"
        },
        "City": "Gurgaon",
        "CountryCode": "IN",
        "CountryName": "India",
        "Nationality": "IN",
        "ContactNo": "9879879877",
        "Email": "harsh@tbtq.in",
        "IsLeadPax": false,
        "FFAirlineCode": null,
        "FFNumber": "",
        "GSTCompanyAddress": "",
        "GSTCompanyContactNumber": "",
        "GSTCompanyName": "",
        "GSTNumber": "",
        "GSTCompanyEmail": ""
      },
      {
        "Title": "Mr",
        "FirstName": "neeraj",
        "LastName": "rao",
        "PaxType": 2,
        "DateOfBirth": "2013-12-09T00:00:00",
        "Gender": 1,
        "PassportNo": "KJHHJKHKJH",
        "PassportExpiry": "2022-02-06T00:00:00",
        "AddressLine1": "123, Test",
        "AddressLine2": "",
        "Fare": {
                  "Currency": "INR",
          "BaseFare": 6000,
                      "Tax": 1244,
                      "YQTax": 0,
                      "AdditionalTxnFeeOfrd": 0,
                      "AdditionalTxnFeePub": 0,
                      "PGCharge": 0,
          "OtherCharges": 944.00,
          "Discount": 0,
                  "PublishedFare": 32902,
                  "CommissionEarned": 0,
                  "PLBEarned": 0,
                  "IncentiveEarned": 0,
                  "OfferedFare": 32902.00,
                  "TdsOnCommission": 0,
                  "TdsOnPLB": 0,
                  "TdsOnIncentive": 0,
                  "ServiceFee": 0
        },
        "Meal": {
          "Code": "CHML",
          "Description": "Child Food"
        },
        "SeatPreference": {
          "Code": "A",
          "Description": "Aisle"
        },
        "City": "Gurgaon",
        "CountryCode": "IN",
        "CountryName": "India",
        "Nationality": "IN",
        "ContactNo": "9879879877",
        "Email": "harsh@tbtq.in",
        "IsLeadPax": false,
        "FFAirlineCode": null,
        "FFNumber": "",
        "GSTCompanyAddress": "",
        "GSTCompanyContactNumber": "",
        "GSTCompanyName": "",
        "GSTNumber": "",
        "GSTCompanyEmail": ""
      },
      {
        "Title": "Mr",
        "FirstName": "sachin",
        "LastName": "singh",
        "PaxType": 3,
        "DateOfBirth": "2019-05-06T00:00:00",
        "Gender": 1,
        "PassportNo": "KJHHJKHKJH",
        "PassportExpiry": "2025-12-06T00:00:00",
        "AddressLine1": "123, Test",
        "AddressLine2": "",
        "Fare": {
                 "Currency": "INR",
         "BaseFare": 2500,
                      "Tax": 482,
                      "YQTax": 0,
                      "AdditionalTxnFeeOfrd": 0,
                      "AdditionalTxnFeePub": 0,
                      "PGCharge": 0,
          "OtherCharges": 944.00,
          "Discount": 0,
                  "PublishedFare": 32902,
                  "CommissionEarned": 0,
                  "PLBEarned": 0,
                  "IncentiveEarned": 0,
                  "OfferedFare": 32902.00,
                  "TdsOnCommission": 0,
                  "TdsOnPLB": 0,
                  "TdsOnIncentive": 0,
                  "ServiceFee": 0
        },
        "City": "Gurgaon",
        "CountryCode": "IN",
        "CountryName": "India",
        "Nationality": "IN",
        "ContactNo": "9879879877",
        "Email": "harsh@tbtq.in",
        "IsLeadPax": false,
        "FFAirlineCode": null,
        "FFNumber": "",
        "GSTCompanyAddress": "",
        "GSTCompanyContactNumber": "",
        "GSTCompanyName": "",
        "GSTNumber": "",
        "GSTCompanyEmail": ""
      }
    ],




  TBO FARES NODES EXPLAINED:

    1. Published Fare: Published fare is the price which agency will charge from end customer, if agency wants to add any additional markup then they can add same at their end.
    Formula: BaseFare + Tax + OtherCharges + ServiceFee + AdditionalTxnFeepub + AirlineTransFee + GST + TDS + Agency additional Markup (if applied from profile)

    2. Offered Fare: Offered Fare is the price which is provided by airline after deduction of only commission.
    Formula: Published Fare - Commission Earned (Commission + PLB + Incentive) - TDS - Agency additional Markup (if applied from profile)
    Note: TDS is not the part of offered fare in search response only

    3. Net Payable: Net Payable is the fare which is payable to TBO by agency.
    Formula: Published Fare – (CommissionEarned+ IncentiveEarned+ PLBEarned + AdditionalTxnFee) + (TdsOnCommission + TdsOnIncentive + TdsOnPLB) + GST(IGSTAmount+CGSTAmount+SGSTAmount+CessAmount)


# Book/ Ticket improvements to be made

1. strongly recommend to setup timeout of 300 seconds
2. make sure to select free meals,  free baggage and free seats from the SSR response and  include these in the ticket request.
2. In case of timeout in Book/ Ticket methods, we recommend to follow below steps to make sure booking is done or not (rather than creating new booking):
   Call GetBookingDetails() method to fetch current booking details/ status, and if you get “Your request could not be processed as booking under process.” message in GetBookingDetails() response, you will have to keep calling GetBookingDetails() method in 10-15 seconds of interval till you don’t receive actual booking details/ status to avoid financial losses.
3. needed field:  Gender, Title, AddressLine1, City, CountryCode, Nationality, CountryName, DateOfBirth
4. LeadPax node will be true for only one passenger.
5. for infant only meal can be selected, no baggage and seat


# the working JSON for request and response for all the cases, LCC and NON-LCC => STUDY THESE AND MAKE CHANGES

#  NON-LCC book request :
  {
"EndUserIp": "103.53.43.82",
"TokenId": "1e217420-9383-4699-bc1b-406e76bfd5d8",
"TraceId": "6b45a298-4f5c-452b-a25b-f39ef5c2b1ff",
"ResultIndex": "OB45[TBO]Cvc9ujhpgmFYmLjqiXrV1o9IB+RJhpWbQAwVo5Y7WOqnYCj6oktS6W24VgqYd29n8nGXMUpQ32jBTsnFKF6hGrtoisv46xFEIwz7Mb7/qdg52h9g+sJsJnA8LLd8O4MrpOiWpTosMYQ4xZwkTXTGfCX6pSf2S5XjxkQtdwYtdU/jrz/ZOrw1/u8/55BP60a73yU5wtCKCGPjU9Rl+aA8HimWFZ40OY32NCE98CgIbo+z2kp8hlguie4yeKp7ZPrq5Mv20vxASYkLRh8ut3ZU14JAJhVPoSVqWBJHoPD8hAxs1x9p5cT8gKCE4SRqHI8sRklL6d7CvQ+Ijnw9pSYp5F+JICRYo5yq8bQtcPQ1TXdijCfvX4vm80QB/8hidaUxpb1+/2jfQX8rdmDtGwIJO5AdFFgpYM1PNt8HPIRNi9RvHNUOJ7O4MMYkeRjw8DU16jDbSEbLWk8rug6bCZSShWGgoimA/vhZeoCMMAg2/1uTt+TkBVVlNlDzYhjrw0bS0WLREepcIzplL3bCKEeJeVPLsJM4HD9rXodrhCMtv5Iorg0JHOj3cr+Rm7ddcqKyKmoDD0a48s62y9+2dEAmS+iVDchXJT94vvJJKrYt8SfpKMTFdb0ydI2bgubmZKRbSKV0ozZ48hrYoeQOe39p9CMi8YbpArCaeMXQPWWKRLw+h99LSkMdNVX7ow6i//ENce2YanUwpvBr2+Y/UElLgauDwm6/156n+/wG1EfBqRM=",
"Passengers": [
        {
            "Title": "Mr",
            "FirstName": "rahul",
            "LastName": "yadav",
            "PaxType": 1,
            "Gender": 1,
            "ContactNo": "1234567822",
            "Email": "harshdemotry@tbtasdvqert.in",
            "DateOfBirth": "1992-11-23T00:00:00",
            "IsLeadPax": true,
            "AddressLine1": "123, Test",
            "City": "Gurgaon",
            "CountryCode": "IN",
            "Fare": {
                "BaseFare": 5481,
                "Tax": 841,
                "YQTax": 0,
                "AdditionalTxnFeeOfrd": 0,
                "AdditionalTxnFeePub": 0,
                "PGCharge": 0
            },
           
       "SeatDynamic": {
            "Description": 2,
            "Code": "28E"
        },
        "Baggage": {
            "Description": 2,
            "Code": "BG05"
        },
        "MealDynamic": {
            "Description": 2,
            "Code": "NVML"
        }
        },
        {
            "Title": "Mrs",
            "FirstName": "sheetal",
            "LastName": "yadav",
            "PaxType": 1,
            "Gender": 1,
            "ContactNo": "1234567822",
            "Email": "harshdemotry@tbtasdvqert.in",
            "DateOfBirth": "1998-01-31T00:00:00",
            "IsLeadPax": true,
            "AddressLine1": "123, Test",
            "City": "Gurgaon",
            "CountryCode": "IN",
            "Fare": {
                "BaseFare": 5481,
                "Tax": 841,
                "YQTax": 0,
                "AdditionalTxnFeeOfrd": 0,
                "AdditionalTxnFeePub": 0,
                "PGCharge": 0
            },
           
       "SeatDynamic": {
            "Description": 2,
            "Code": "28D"
        },
        "MealDynamic": {
            "Description": 2,
            "Code": "NVML"
        }
        },
        {
            "Title": "Mr",
            "FirstName": "keshav",
            "LastName": "yadav",
            "PaxType": 2,
            "Gender": 1,
            "ContactNo": "1234567822",
            "Email": "harshdemotry@tbtasdvqert.in",
            "DateOfBirth": "2016-11-03T00:00:00",
            "IsLeadPax": true,
            "AddressLine1": "123, Test",
            "City": "Gurgaon",
            "CountryCode": "IN",
            "Fare": {
                "BaseFare": 4933,
                "Tax": 814,
                "YQTax": 0,
                "AdditionalTxnFeeOfrd": 0,
                "AdditionalTxnFeePub": 0,
                "PGCharge": 0
            },
            
       "SeatDynamic": {
            "Description": 2,
            "Code": "28C"
        },
        "MealDynamic": {
            "Description": 2,
            "Code": "NVML"
        }
        }
    ]
}
#  NON-LCC book response :

{
    "Response": {
        "Error": {
            "ErrorCode": 0,
            "ErrorMessage": ""
        },
        "TraceId": "6b45a298-4f5c-452b-a25b-f39ef5c2b1ff",
        "ResponseStatus": 1,
        "Response": {
            "ItineraryChangeList": null,
            "PNR": "7UJ64E",
            "BookingId": 2090725,
            "SSRDenied": false,
            "SSRMessage": null,
            "Status": 1,
            "IsPriceChanged": false,
            "IsTimeChanged": false,
            "FlightItinerary": {
                "CommentDetails": null,
                "FareClassification": "PublishNDC#lightblue",
                "IsSeatsBooked": false,
                "JourneyType": 1,
                "SearchCombinationType": 2,
                "SupplierFareClasses": null,
                "TBOConfNo": "TBFTKFVV9",
                "TBOTripID": null,
                "TripIndicator": 1,
                "BookingAllowedForRoamer": true,
                "BookingId": 2090725,
                "IsCouponAppilcable": true,
                "IsManual": false,
                "PNR": "7UJ64E",
                "IsDomestic": true,
                "ResultFareType": "RegularFare",
                "Source": 77,
                "Origin": "DEL",
                "Destination": "MAA",
                "AirlineCode": "AI",
                "LastTicketDate": "2026-03-11T22:55:00",
                "ValidatingAirlineCode": "AI",
                "AirlineRemark": "We are testing Airline remark node",
                "IsLCC": false,
                "NonRefundable": false,
                "FareType": "RV",
                "CreditNoteNo": null,
                "Fare": {
                    "CFARAmount": 0,
                    "DCFARAmount": 0,
                    "ServiceFeeDisplayType": 0,
                    "Currency": "INR",
                    "BaseFare": 15895.0,
                    "Tax": 2496,
                    "TaxBreakup": [
                        {
                            "key": "K3",
                            "value": 0
                        },
                        {
                            "key": "NotSet",
                            "value": 0.0
                        },
                        {
                            "key": "TotalTax",
                            "value": 2496
                        }
                    ],
                    "YQTax": 0.0,
                    "AdditionalTxnFeeOfrd": 0,
                    "AdditionalTxnFeePub": 0,
                    "PGCharge": 0,
                    "OtherCharges": 0.00,
                    "ChargeBU": [
                        {
                            "key": "TBOMARKUP",
                            "value": 0
                        },
                        {
                            "key": "GLOBALPROCUREMENTCHARGE",
                            "value": 0.00
                        },
                        {
                            "key": "OTHERCHARGE",
                            "value": 0.00
                        },
                        {
                            "key": "CONVENIENCECHARGE",
                            "value": 0
                        }
                    ],
                    "Discount": 0,
                    "PublishedFare": 18391,
                    "CommissionEarned": 135.17,
                    "PLBEarned": 0,
                    "IncentiveEarned": 0,
                    "OfferedFare": 18309.89,
                    "TdsOnCommission": 54.06,
                    "TdsOnPLB": 0,
                    "TdsOnIncentive": 0,
                    "ServiceFee": 0,
                    "TotalBaggageCharges": 0.0,
                    "TotalMealCharges": 0.0,
                    "TotalSeatCharges": 0.0,
                    "TotalSpecialServiceCharges": 0.0
                },
                "CreditNoteCreatedOn": null,
                "Passenger": [
                    {
                        "BarcodeDetails": {
                            "Id": 0,
                            "Barcode": [
                                {
                                    "Index": 1,
                                    "Format": "PDF417",
                                    "Content": "M1YADAV/RAHUL          7UJ64E DELMAAAI 2837 079Y000000000000",
                                    "BarCodeInBase64": null,
                                    "JourneyWayType": 3
                                }
                            ]
                        },
                        "DocumentDetails": null,
                        "GuardianDetails": null,
                        "IsReissued": false,
                        "SegmentDetails": [
                            {
                                "CheckedInBaggage": {
                                    "Unit": "KG",
                                    "Value": "15"
                                },
                                "FlightInfoIndex": "1"
                            }
                        ],
                        "PaxId": 3370777,
                        "Title": "Mr",
                        "FirstName": "rahul",
                        "LastName": "yadav",
                        "PaxType": 1,
                        "DateOfBirth": "1992-11-23T00:00:00",
                        "Gender": 1,
                        "IsPANRequired": false,
                        "IsPassportRequired": false,
                        "PAN": "",
                        "PassportNo": "",
                        "AddressLine1": "123, Test",
                        "Fare": {
                            "CFARAmount": 0,
                            "DCFARAmount": 0,
                            "ServiceFeeDisplayType": 0,
                            "Currency": "INR",
                            "BaseFare": 5481.0,
                            "Tax": 841,
                            "TaxBreakup": [
                                {
                                    "key": "K3",
                                    "value": 0
                                },
                                {
                                    "key": "NotSet",
                                    "value": 0.0
                                },
                                {
                                    "key": "TotalTax",
                                    "value": 841
                                }
                            ],
                            "YQTax": 0.0,
                            "AdditionalTxnFeeOfrd": 0,
                            "AdditionalTxnFeePub": 0,
                            "PGCharge": 0,
                            "OtherCharges": 0.00,
                            "ChargeBU": [
                                {
                                    "key": "TBOMARKUP",
                                    "value": 0
                                },
                                {
                                    "key": "GLOBALPROCUREMENTCHARGE",
                                    "value": 0.00
                                },
                                {
                                    "key": "OTHERCHARGE",
                                    "value": 0.00
                                },
                                {
                                    "key": "CONVENIENCECHARGE",
                                    "value": 0
                                }
                            ],
                            "Discount": 0,
                            "PublishedFare": 6322,
                            "CommissionEarned": 46.61,
                            "PLBEarned": 0,
                            "IncentiveEarned": 0,
                            "OfferedFare": 6294.03,
                            "TdsOnCommission": 18.64,
                            "TdsOnPLB": 0,
                            "TdsOnIncentive": 0,
                            "ServiceFee": 0,
                            "TotalBaggageCharges": 0.0,
                            "TotalMealCharges": 0.0,
                            "TotalSeatCharges": 0.0,
                            "TotalSpecialServiceCharges": 0.0
                        },
                        "City": "Gurgaon",
                        "CountryCode": "IN",
                        "Nationality": "IN",
                        "ContactNo": "+91 1234567822",
                        "Email": "harshdemotry@tbtasdvqert.in",
                        "IsLeadPax": true,
                        "FFAirlineCode": null,
                        "FFNumber": null,
                        "Baggage": [
                            {
                                "AirlineCode": "AI",
                                "FlightNumber": "2837",
                                "WayType": 1,
                                "Code": "NoBaggage",
                                "Description": 2,
                                "Weight": 0,
                                "Currency": "INR",
                                "Price": 0.0,
                                "Origin": "DEL",
                                "Destination": "MAA"
                            }
                        ],
                        "Ssr": [],
                        "SegmentAdditionalInfo": [
                            {
                                "FareBasis": "TU1YXSII",
                                "NVA": "",
                                "NVB": "",
                                "Baggage": "15 KG",
                                "Meal": "0 Platter",
                                "Seat": "",
                                "SpecialService": "",
                                "CabinBaggage": ""
                            }
                        ]
                    },
                    {
                        "BarcodeDetails": {
                            "Id": 0,
                            "Barcode": [
                                {
                                    "Index": 1,
                                    "Format": "PDF417",
                                    "Content": "M1YADAV/SHEETAL        7UJ64E DELMAAAI 2837 079Y000000000000",
                                    "BarCodeInBase64": null,
                                    "JourneyWayType": 3
                                }
                            ]
                        },
                        "DocumentDetails": null,
                        "GuardianDetails": null,
                        "IsReissued": false,
                        "SegmentDetails": [
                            {
                                "CheckedInBaggage": {
                                    "Unit": "KG",
                                    "Value": "15"
                                },
                                "FlightInfoIndex": "1"
                            }
                        ],
                        "PaxId": 3370778,
                        "Title": "Mrs",
                        "FirstName": "sheetal",
                        "LastName": "yadav",
                        "PaxType": 1,
                        "DateOfBirth": "1998-01-31T00:00:00",
                        "Gender": 1,
                        "IsPANRequired": false,
                        "IsPassportRequired": false,
                        "PAN": "",
                        "PassportNo": "",
                        "AddressLine1": "123, Test",
                        "Fare": {
                            "CFARAmount": 0,
                            "DCFARAmount": 0,
                            "ServiceFeeDisplayType": 0,
                            "Currency": "INR",
                            "BaseFare": 5481.0,
                            "Tax": 841,
                            "TaxBreakup": [
                                {
                                    "key": "K3",
                                    "value": 0
                                },
                                {
                                    "key": "NotSet",
                                    "value": 0.0
                                },
                                {
                                    "key": "TotalTax",
                                    "value": 841
                                }
                            ],
                            "YQTax": 0.0,
                            "AdditionalTxnFeeOfrd": 0,
                            "AdditionalTxnFeePub": 0,
                            "PGCharge": 0,
                            "OtherCharges": 0.00,
                            "ChargeBU": [
                                {
                                    "key": "TBOMARKUP",
                                    "value": 0
                                },
                                {
                                    "key": "GLOBALPROCUREMENTCHARGE",
                                    "value": 0.00
                                },
                                {
                                    "key": "OTHERCHARGE",
                                    "value": 0.00
                                },
                                {
                                    "key": "CONVENIENCECHARGE",
                                    "value": 0
                                }
                            ],
                            "Discount": 0,
                            "PublishedFare": 6322,
                            "CommissionEarned": 46.61,
                            "PLBEarned": 0,
                            "IncentiveEarned": 0,
                            "OfferedFare": 6294.03,
                            "TdsOnCommission": 18.64,
                            "TdsOnPLB": 0,
                            "TdsOnIncentive": 0,
                            "ServiceFee": 0,
                            "TotalBaggageCharges": 0.0,
                            "TotalMealCharges": 0.0,
                            "TotalSeatCharges": 0.0,
                            "TotalSpecialServiceCharges": 0.0
                        },
                        "City": "Gurgaon",
                        "CountryCode": "IN",
                        "Nationality": "IN",
                        "ContactNo": "1234567822",
                        "Email": "harshdemotry@tbtasdvqert.in",
                        "IsLeadPax": true,
                        "FFAirlineCode": null,
                        "FFNumber": null,
                        "Baggage": [
                            {
                                "AirlineCode": "AI",
                                "FlightNumber": "2837",
                                "WayType": 1,
                                "Code": "NoBaggage",
                                "Description": 2,
                                "Weight": 0,
                                "Currency": "INR",
                                "Price": 0.0,
                                "Origin": "DEL",
                                "Destination": "MAA"
                            }
                        ],
                        "Ssr": [],
                        "SegmentAdditionalInfo": [
                            {
                                "FareBasis": "TU1YXSII",
                                "NVA": "",
                                "NVB": "",
                                "Baggage": "15 KG",
                                "Meal": "0 Platter",
                                "Seat": "",
                                "SpecialService": "",
                                "CabinBaggage": ""
                            }
                        ]
                    },
                    {
                        "BarcodeDetails": {
                            "Id": 0,
                            "Barcode": [
                                {
                                    "Index": 1,
                                    "Format": "PDF417",
                                    "Content": "M1YADAV/KESHAV         7UJ64E DELMAAAI 2837 079Y000000000000",
                                    "BarCodeInBase64": null,
                                    "JourneyWayType": 3
                                }
                            ]
                        },
                        "DocumentDetails": null,
                        "GuardianDetails": null,
                        "IsReissued": false,
                        "SegmentDetails": [
                            {
                                "CheckedInBaggage": {
                                    "Unit": "KG",
                                    "Value": "15"
                                },
                                "FlightInfoIndex": "1"
                            }
                        ],
                        "PaxId": 3370779,
                        "Title": "Mr",
                        "FirstName": "keshav",
                        "LastName": "yadav",
                        "PaxType": 2,
                        "DateOfBirth": "2016-11-03T00:00:00",
                        "Gender": 1,
                        "IsPANRequired": false,
                        "IsPassportRequired": false,
                        "PAN": "",
                        "PassportNo": "",
                        "AddressLine1": "123, Test",
                        "Fare": {
                            "CFARAmount": 0,
                            "DCFARAmount": 0,
                            "ServiceFeeDisplayType": 0,
                            "Currency": "INR",
                            "BaseFare": 4933.0,
                            "Tax": 814,
                            "TaxBreakup": [
                                {
                                    "key": "K3",
                                    "value": 0
                                },
                                {
                                    "key": "NotSet",
                                    "value": 0.0
                                },
                                {
                                    "key": "TotalTax",
                                    "value": 814
                                }
                            ],
                            "YQTax": 0.0,
                            "AdditionalTxnFeeOfrd": 0,
                            "AdditionalTxnFeePub": 0,
                            "PGCharge": 0,
                            "OtherCharges": 0.00,
                            "ChargeBU": [
                                {
                                    "key": "TBOMARKUP",
                                    "value": 0
                                },
                                {
                                    "key": "GLOBALPROCUREMENTCHARGE",
                                    "value": 0.00
                                },
                                {
                                    "key": "OTHERCHARGE",
                                    "value": 0.00
                                },
                                {
                                    "key": "CONVENIENCECHARGE",
                                    "value": 0
                                }
                            ],
                            "Discount": 0,
                            "PublishedFare": 5747,
                            "CommissionEarned": 41.95,
                            "PLBEarned": 0,
                            "IncentiveEarned": 0,
                            "OfferedFare": 5721.83,
                            "TdsOnCommission": 16.78,
                            "TdsOnPLB": 0,
                            "TdsOnIncentive": 0,
                            "ServiceFee": 0,
                            "TotalBaggageCharges": 0.0,
                            "TotalMealCharges": 0.0,
                            "TotalSeatCharges": 0.0,
                            "TotalSpecialServiceCharges": 0.0
                        },
                        "City": "Gurgaon",
                        "CountryCode": "IN",
                        "Nationality": "IN",
                        "ContactNo": "1234567822",
                        "Email": "harshdemotry@tbtasdvqert.in",
                        "IsLeadPax": true,
                        "FFAirlineCode": null,
                        "FFNumber": null,
                        "Baggage": [
                            {
                                "AirlineCode": "AI",
                                "FlightNumber": "2837",
                                "WayType": 1,
                                "Code": "NoBaggage",
                                "Description": 2,
                                "Weight": 0,
                                "Currency": "INR",
                                "Price": 0.0,
                                "Origin": "DEL",
                                "Destination": "MAA"
                            }
                        ],
                        "Ssr": [],
                        "SegmentAdditionalInfo": [
                            {
                                "FareBasis": "TU1YXSII",
                                "NVA": "",
                                "NVB": "",
                                "Baggage": "15 KG",
                                "Meal": "0 Platter",
                                "Seat": "",
                                "SpecialService": "",
                                "CabinBaggage": ""
                            }
                        ]
                    }
                ],
                "CancellationCharges": null,
                "Segments": [
                    {
                        "Baggage": "15 KG",
                        "CabinBaggage": "Included",
                        "CabinClass": 0,
                        "SupplierFareClass": null,
                        "TripIndicator": 1,
                        "SegmentIndicator": 1,
                        "Airline": {
                            "AirlineCode": "AI",
                            "AirlineName": "Air India",
                            "FlightNumber": "2837",
                            "FareClass": "T",
                            "OperatingCarrier": "AI"
                        },
                        "AirlinePNR": "7UIIJV",
                        "Origin": {
                            "Airport": {
                                "AirportCode": "DEL",
                                "AirportName": "Indira Gandhi Airport",
                                "Terminal": "3",
                                "CityCode": "DEL",
                                "CityName": "Delhi",
                                "CountryCode": "IN",
                                "CountryName": "India"
                            },
                            "DepTime": "2026-03-20T17:55:00"
                        },
                        "Destination": {
                            "Airport": {
                                "AirportCode": "MAA",
                                "AirportName": "Chennai International Airport",
                                "Terminal": "4",
                                "CityCode": "MAA",
                                "CityName": "Chennai",
                                "CountryCode": "IN",
                                "CountryName": "India"
                            },
                            "ArrTime": "2026-03-20T20:40:00"
                        },
                        "AccumulatedDuration": 165,
                        "Duration": 165,
                        "GroundTime": 0,
                        "Mile": 0,
                        "StopOver": false,
                        "FlightInfoIndex": "1",
                        "StopPoint": "",
                        "StopPointArrivalTime": "0001-01-01T00:00:00",
                        "StopPointDepartureTime": "0001-01-01T00:00:00",
                        "Craft": "32N",
                        "Remark": null,
                        "IsETicketEligible": true,
                        "FlightStatus": "Confirmed",
                        "Status": "HK",
                        "FareClassification": null
                    }
                ],
                "FareRules": [
                    {
                        "Origin": "DEL",
                        "Destination": "MAA",
                        "Airline": "AI",
                        "FareBasisCode": "TU1YXSII",
                        "FareRuleDetail": "<b><u>Adult</b></u><br /><br />Cancel before departure: Allowed with Restriction<br />Cancel before departure - No Show: Not Allowed<br />Cancel after departure: Not Allowed<br />Cancel after departure - No Show: Not Allowed<br />Change before departure: Allowed with Restriction<br />Change before departure - No Show: Allowed with Restriction<br />Change after departure: Not Allowed<br />Change after departure - No Show: Not Allowed<br /><br /><b><u>Child</b></u><br /><br />Cancel before departure: Not Allowed<br />Cancel before departure - No Show: Not Allowed<br />Cancel after departure: Not Allowed<br />Cancel after departure - No Show: Not Allowed<br />Change before departure: Allowed with Restriction<br />Change before departure - No Show: Allowed with Restriction<br />Change after departure: Not Allowed<br />Change after departure - No Show: Not Allowed<br/> <br/><ul><li>GST, RAF AND ANY OTHER APPLICABLE CHARGES ARE EXTRA.</li><li>FEES ARE INDICATIVE PER PAX AND PER SECTOR.</li><li>FOR DOMESTIC BOOKINGS, PASSENGERS MUST SUBMIT THE CANCELLATION OR REISSUE REQUEST AT LEAST 2 HOURS BEFORE THE TIME LIMIT DEFINED IN THE AIRLINE's POLICY.</li><li>FOR INTERNATIONAL BOOKINGS, PASSENGERS MUST SUBMIT THE CANCELLATION OR REISSUE REQUEST AT LEAST 4 HOURS BEFORE THE TIME LIMIT DEFINED IN THE AIRLINE's POLICY.</li></ul>",
                        "FareRestriction": "",
                        "FareFamilyCode": ""
                    }
                ],
                "MiniFareRules": [
                    {
                        "CFARExcludedDetails": null,
                        "JourneyPoints": "DEL-MAA",
                        "Type": "Reissue",
                        "From": "",
                        "To": "",
                        "Unit": "",
                        "Details": "INR 3000*",
                        "OnlineReissueAllowed": true,
                        "OnlineRefundAllowed": false
                    },
                    {
                        "CFARExcludedDetails": null,
                        "JourneyPoints": "DEL-MAA",
                        "Type": "Cancellation",
                        "From": "",
                        "To": "",
                        "Unit": "",
                        "Details": "INR 5000*",
                        "OnlineReissueAllowed": false,
                        "OnlineRefundAllowed": true
                    }
                ],
                "PenaltyCharges": {},
                "Status": 1,
                "IsWebCheckInAllowed": false
            }
        }
    }
}

#  NON-LCC ticket request :
  {
    "EndUserIp": "192.168.5.1",
    "TokenId": "1e217420-9383-4699-bc1b-406e76bfd5d8",
    "TraceId": "6b45a298-4f5c-452b-a25b-f39ef5c2b1ff",
    "PNR": "7UJ64E",
    "BookingId": 2090725
  }
#  NON-LCC ticket response :

  {
    "Response": {
        "B2B2BStatus": false,
        "Error": {
            "ErrorCode": 0,
            "ErrorMessage": ""
        },
        "ResponseStatus": 1,
        "TraceId": "6b45a298-4f5c-452b-a25b-f39ef5c2b1ff",
        "Response": {
            "ItineraryChangeList": null,
            "PNR": "7UJ64E",
            "BookingId": 2090725,
            "SSRDenied": false,
            "SSRMessage": null,
            "IsPriceChanged": false,
            "IsTimeChanged": false,
            "FlightItinerary": {
                "AgentRemarks": "",
                "CommentDetails": null,
                "FareClassification": "PublishNDC#lightblue",
                "IsAutoReissuanceAllowed": true,
                "IsPartialVoidAllowed": true,
                "IsSeatsBooked": false,
                "IssuancePcc": "DELWI2216",
                "JourneyType": 1,
                "SearchCombinationType": 2,
                "SupplierFareClasses": "",
                "TBOConfNo": "TBFTKFVV9",
                "TBOTripID": null,
                "TripIndicator": 1,
                "BookingAllowedForRoamer": true,
                "BookingId": 2090725,
                "IsCouponAppilcable": true,
                "IsManual": false,
                "PNR": "7UJ64E",
                "IsDomestic": true,
                "ResultFareType": "RegularFare",
                "Source": 77,
                "Origin": "DEL",
                "Destination": "MAA",
                "AirlineCode": "AI",
                "LastTicketDate": "2026-03-11T22:55:00",
                "ValidatingAirlineCode": "AI",
                "AirlineRemark": "We are testing Airline remark node",
                "IsLCC": false,
                "NonRefundable": false,
                "FareType": "RV",
                "CreditNoteNo": null,
                "Fare": {
                    "CFARAmount": 0,
                    "DCFARAmount": 0,
                    "ServiceFeeDisplayType": 0,
                    "Currency": "INR",
                    "BaseFare": 15895,
                    "Tax": 2496,
                    "TaxBreakup": [
                        {
                            "key": "K3",
                            "value": 822
                        },
                        {
                            "key": "YR",
                            "value": 510
                        },
                        {
                            "key": "INTax",
                            "value": 456
                        },
                        {
                            "key": "TotalTax",
                            "value": 0
                        },
                        {
                            "key": "OtherTaxes",
                            "value": 708
                        }
                    ],
                    "YQTax": 0,
                    "AdditionalTxnFeeOfrd": 0,
                    "AdditionalTxnFeePub": 0,
                    "PGCharge": 0,
                    "OtherCharges": 0,
                    "ChargeBU": [
                        {
                            "key": "TBOMARKUP",
                            "value": 0
                        },
                        {
                            "key": "GLOBALPROCUREMENTCHARGE",
                            "value": 0
                        },
                        {
                            "key": "OTHERCHARGE",
                            "value": 0
                        },
                        {
                            "key": "CONVENIENCECHARGE",
                            "value": 0
                        }
                    ],
                    "Discount": 0,
                    "PublishedFare": 18391,
                    "CommissionEarned": 135.17,
                    "PLBEarned": 0,
                    "IncentiveEarned": 0,
                    "OfferedFare": 18309.89,
                    "TdsOnCommission": 54.06,
                    "TdsOnPLB": 0,
                    "TdsOnIncentive": 0,
                    "ServiceFee": 0,
                    "TotalBaggageCharges": 0,
                    "TotalMealCharges": 0,
                    "TotalSeatCharges": 0,
                    "TotalSpecialServiceCharges": 0
                },
                "CreditNoteCreatedOn": null,
                "Passenger": [
                    {
                        "BarcodeDetails": {
                            "Id": 3370777,
                            "Barcode": [
                                {
                                    "Index": 1,
                                    "Format": "PDF417",
                                    "Content": "M1YADAV/RAHUL          7UJ64E DELMAAAI 2837 079Y000000000000",
                                    "BarCodeInBase64": null,
                                    "JourneyWayType": 3
                                }
                            ]
                        },
                        "DocumentDetails": null,
                        "GuardianDetails": null,
                        "IsReissued": false,
                        "SegmentDetails": null,
                        "PaxId": 3370777,
                        "Title": "Mr",
                        "FirstName": "rahul",
                        "LastName": "yadav",
                        "PaxType": 1,
                        "DateOfBirth": "1992-11-23T00:00:00",
                        "Gender": 1,
                        "IsPANRequired": false,
                        "IsPassportRequired": false,
                        "PAN": "",
                        "PassportNo": "",
                        "AddressLine1": "123, Test",
                        "Fare": {
                            "CFARAmount": 0,
                            "DCFARAmount": 0,
                            "ServiceFeeDisplayType": 0,
                            "Currency": "INR",
                            "BaseFare": 5481,
                            "Tax": 841,
                            "TaxBreakup": [
                                {
                                    "key": "K3",
                                    "value": 283
                                },
                                {
                                    "key": "YR",
                                    "value": 170
                                },
                                {
                                    "key": "INTax",
                                    "value": 152
                                },
                                {
                                    "key": "TotalTax",
                                    "value": 0
                                },
                                {
                                    "key": "OtherTaxes",
                                    "value": 236
                                }
                            ],
                            "YQTax": 0,
                            "AdditionalTxnFeeOfrd": 0,
                            "AdditionalTxnFeePub": 0,
                            "PGCharge": 0,
                            "OtherCharges": 0,
                            "ChargeBU": [
                                {
                                    "key": "TBOMARKUP",
                                    "value": 0
                                },
                                {
                                    "key": "GLOBALPROCUREMENTCHARGE",
                                    "value": 0
                                },
                                {
                                    "key": "OTHERCHARGE",
                                    "value": 0
                                },
                                {
                                    "key": "CONVENIENCECHARGE",
                                    "value": 0
                                }
                            ],
                            "Discount": 0,
                            "PublishedFare": 6322,
                            "CommissionEarned": 46.61,
                            "PLBEarned": 0,
                            "IncentiveEarned": 0,
                            "OfferedFare": 6294.03,
                            "TdsOnCommission": 18.64,
                            "TdsOnPLB": 0,
                            "TdsOnIncentive": 0,
                            "ServiceFee": 0,
                            "TotalBaggageCharges": 0,
                            "TotalMealCharges": 0,
                            "TotalSeatCharges": 0,
                            "TotalSpecialServiceCharges": 0
                        },
                        "City": "Gurgaon",
                        "CountryCode": "IN",
                        "Nationality": "IN",
                        "ContactNo": "+91 1234567822",
                        "Email": "harshdemotry@tbtasdvqert.in",
                        "IsLeadPax": true,
                        "FFAirlineCode": null,
                        "FFNumber": null,
                        "Ssr": [],
                        "Ticket": {
                            "TicketId": 2382147,
                            "TicketNumber": "2179060036",
                            "IssueDate": "2026-03-10T05:30:00",
                            "ValidatingAirline": "098",
                            "Remarks": "",
                            "ServiceFeeDisplayType": "ShowInTax",
                            "Status": "OK",
                            "ConjunctionNumber": "",
                            "TicketType": "N"
                        },
                        "SegmentAdditionalInfo": [
                            {
                                "FareBasis": "TU1YXSII",
                                "NVA": "",
                                "NVB": "",
                                "Baggage": "15 KG",
                                "Meal": null,
                                "Seat": null,
                                "SpecialService": null,
                                "CabinBaggage": "Not Known"
                            }
                        ]
                    },
                    {
                        "BarcodeDetails": {
                            "Id": 3370778,
                            "Barcode": [
                                {
                                    "Index": 1,
                                    "Format": "PDF417",
                                    "Content": "M1YADAV/SHEETAL        7UJ64E DELMAAAI 2837 079Y000000000000",
                                    "BarCodeInBase64": null,
                                    "JourneyWayType": 3
                                }
                            ]
                        },
                        "DocumentDetails": null,
                        "GuardianDetails": null,
                        "IsReissued": false,
                        "SegmentDetails": null,
                        "PaxId": 3370778,
                        "Title": "Mrs",
                        "FirstName": "sheetal",
                        "LastName": "yadav",
                        "PaxType": 1,
                        "DateOfBirth": "1998-01-31T00:00:00",
                        "Gender": 1,
                        "IsPANRequired": false,
                        "IsPassportRequired": false,
                        "PAN": "",
                        "PassportNo": "",
                        "AddressLine1": "123, Test",
                        "Fare": {
                            "CFARAmount": 0,
                            "DCFARAmount": 0,
                            "ServiceFeeDisplayType": 0,
                            "Currency": "INR",
                            "BaseFare": 5481,
                            "Tax": 841,
                            "TaxBreakup": [
                                {
                                    "key": "K3",
                                    "value": 283
                                },
                                {
                                    "key": "YR",
                                    "value": 170
                                },
                                {
                                    "key": "INTax",
                                    "value": 152
                                },
                                {
                                    "key": "TotalTax",
                                    "value": 0
                                },
                                {
                                    "key": "OtherTaxes",
                                    "value": 236
                                }
                            ],
                            "YQTax": 0,
                            "AdditionalTxnFeeOfrd": 0,
                            "AdditionalTxnFeePub": 0,
                            "PGCharge": 0,
                            "OtherCharges": 0,
                            "ChargeBU": [
                                {
                                    "key": "TBOMARKUP",
                                    "value": 0
                                },
                                {
                                    "key": "GLOBALPROCUREMENTCHARGE",
                                    "value": 0
                                },
                                {
                                    "key": "OTHERCHARGE",
                                    "value": 0
                                },
                                {
                                    "key": "CONVENIENCECHARGE",
                                    "value": 0
                                }
                            ],
                            "Discount": 0,
                            "PublishedFare": 6322,
                            "CommissionEarned": 46.61,
                            "PLBEarned": 0,
                            "IncentiveEarned": 0,
                            "OfferedFare": 6294.03,
                            "TdsOnCommission": 18.64,
                            "TdsOnPLB": 0,
                            "TdsOnIncentive": 0,
                            "ServiceFee": 0,
                            "TotalBaggageCharges": 0, // means seat not booked?
                            "TotalMealCharges": 0,
                            "TotalSeatCharges": 0,
                            "TotalSpecialServiceCharges": 0
                        },
                        "City": "Gurgaon",
                        "CountryCode": "IN",
                        "Nationality": "IN",
                        "ContactNo": "1234567822",
                        "Email": "harshdemotry@tbtasdvqert.in",
                        "IsLeadPax": true,
                        "FFAirlineCode": null,
                        "FFNumber": null,
                        "Ssr": [],
                        "Ticket": {
                            "TicketId": 2382148,
                            "TicketNumber": "2179060037",
                            "IssueDate": "2026-03-10T05:30:00",
                            "ValidatingAirline": "098",
                            "Remarks": "",
                            "ServiceFeeDisplayType": "ShowInTax",
                            "Status": "OK",
                            "ConjunctionNumber": "",
                            "TicketType": "N"
                        },
                        "SegmentAdditionalInfo": [
                            {
                                "FareBasis": "TU1YXSII",
                                "NVA": "",
                                "NVB": "",
                                "Baggage": "15 KG",
                                "Meal": null,
                                "Seat": null,
                                "SpecialService": null,
                                "CabinBaggage": "Not Known"
                            }
                        ]
                    },
                    {
                        "BarcodeDetails": {
                            "Id": 3370779,
                            "Barcode": [
                                {
                                    "Index": 1,
                                    "Format": "PDF417",
                                    "Content": "M1YADAV/KESHAV         7UJ64E DELMAAAI 2837 079Y000000000000",
                                    "BarCodeInBase64": null,
                                    "JourneyWayType": 3
                                }
                            ]
                        },
                        "DocumentDetails": null,
                        "GuardianDetails": null,
                        "IsReissued": false,
                        "SegmentDetails": null,
                        "PaxId": 3370779,
                        "Title": "Mr",
                        "FirstName": "keshav",
                        "LastName": "yadav",
                        "PaxType": 2,
                        "DateOfBirth": "2016-11-03T00:00:00",
                        "Gender": 1,
                        "IsPANRequired": false,
                        "IsPassportRequired": false,
                        "PAN": "",
                        "PassportNo": "",
                        "AddressLine1": "123, Test",
                        "Fare": {
                            "CFARAmount": 0,
                            "DCFARAmount": 0,
                            "ServiceFeeDisplayType": 0,
                            "Currency": "INR",
                            "BaseFare": 4933,
                            "Tax": 814,
                            "TaxBreakup": [
                                {
                                    "key": "K3",
                                    "value": 256
                                },
                                {
                                    "key": "YR",
                                    "value": 170
                                },
                                {
                                    "key": "INTax",
                                    "value": 152
                                },
                                {
                                    "key": "TotalTax",
                                    "value": 0
                                },
                                {
                                    "key": "OtherTaxes",
                                    "value": 236
                                }
                            ],
                            "YQTax": 0,
                            "AdditionalTxnFeeOfrd": 0,
                            "AdditionalTxnFeePub": 0,
                            "PGCharge": 0,
                            "OtherCharges": 0,
                            "ChargeBU": [
                                {
                                    "key": "TBOMARKUP",
                                    "value": 0
                                },
                                {
                                    "key": "GLOBALPROCUREMENTCHARGE",
                                    "value": 0
                                },
                                {
                                    "key": "OTHERCHARGE",
                                    "value": 0
                                },
                                {
                                    "key": "CONVENIENCECHARGE",
                                    "value": 0
                                }
                            ],
                            "Discount": 0,
                            "PublishedFare": 5747,
                            "CommissionEarned": 41.95,
                            "PLBEarned": 0,
                            "IncentiveEarned": 0,
                            "OfferedFare": 5721.83,
                            "TdsOnCommission": 16.78,
                            "TdsOnPLB": 0,
                            "TdsOnIncentive": 0,
                            "ServiceFee": 0,
                            "TotalBaggageCharges": 0,
                            "TotalMealCharges": 0,
                            "TotalSeatCharges": 0,
                            "TotalSpecialServiceCharges": 0
                        },
                        "City": "Gurgaon",
                        "CountryCode": "IN",
                        "Nationality": "IN",
                        "ContactNo": "1234567822",
                        "Email": "harshdemotry@tbtasdvqert.in",
                        "IsLeadPax": true,
                        "FFAirlineCode": null,
                        "FFNumber": null,
                        "Ssr": [
                            {
                                "Detail": "03/11/2016",
                                "SsrCode": "CHLD",
                                "SsrStatus": null,
                                "Status": 3
                            }
                        ],
                        "Ticket": {
                            "TicketId": 2382149,
                            "TicketNumber": "2179060038",
                            "IssueDate": "2026-03-10T05:30:00",
                            "ValidatingAirline": "098",
                            "Remarks": "",
                            "ServiceFeeDisplayType": "ShowInTax",
                            "Status": "OK",
                            "ConjunctionNumber": "",
                            "TicketType": "N"
                        },
                        "SegmentAdditionalInfo": [
                            {
                                "FareBasis": "TU1YXSII",
                                "NVA": "",
                                "NVB": "",
                                "Baggage": "15 KG",
                                "Meal": null,
                                "Seat": null,
                                "SpecialService": null,
                                "CabinBaggage": "Not Known"
                            }
                        ]
                    }
                ],
                "CancellationCharges": null,
                "Segments": [
                    {
                        "Baggage": "15 KG",
                        "CabinBaggage": "Included",
                        "CabinClass": 0,
                        "SupplierFareClass": null,
                        "TripIndicator": 1,
                        "SegmentIndicator": 1,
                        "Airline": {
                            "AirlineCode": "AI",
                            "AirlineName": "Air India",
                            "FlightNumber": "2837",
                            "FareClass": "T",
                            "OperatingCarrier": "AI"
                        },
                        "AirlinePNR": "7UIIJV",
                        "Origin": {
                            "Airport": {
                                "AirportCode": "DEL",
                                "AirportName": "Indira Gandhi Airport",
                                "Terminal": "3",
                                "CityCode": "DEL",
                                "CityName": "Delhi",
                                "CountryCode": "IN",
                                "CountryName": "India"
                            },
                            "DepTime": "2026-03-20T17:55:00"
                        },
                        "Destination": {
                            "Airport": {
                                "AirportCode": "MAA",
                                "AirportName": "Chennai International Airport",
                                "Terminal": "4",
                                "CityCode": "MAA",
                                "CityName": "Chennai",
                                "CountryCode": "IN",
                                "CountryName": "India"
                            },
                            "ArrTime": "2026-03-20T20:40:00"
                        },
                        "AccumulatedDuration": 165,
                        "Duration": 165,
                        "GroundTime": 0,
                        "Mile": 0,
                        "StopOver": false,
                        "FlightInfoIndex": "1",
                        "StopPoint": "",
                        "StopPointArrivalTime": null,
                        "StopPointDepartureTime": null,
                        "Craft": "32N",
                        "Remark": null,
                        "IsETicketEligible": true,
                        "FlightStatus": "Confirmed",
                        "Status": "HK",
                        "FareClassification": null
                    }
                ],
                "FareRules": [
                    {
                        "Origin": "DEL",
                        "Destination": "MAA",
                        "Airline": "AI",
                        "FareBasisCode": "TU1YXSII",
                        "FareRuleDetail": "<b><u>Adult</b></u><br /><br />Cancel before departure: Allowed with Restriction<br />Cancel before departure - No Show: Not Allowed<br />Cancel after departure: Not Allowed<br />Cancel after departure - No Show: Not Allowed<br />Change before departure: Allowed with Restriction<br />Change before departure - No Show: Allowed with Restriction<br />Change after departure: Not Allowed<br />Change after departure - No Show: Not Allowed<br /><br /><b><u>Child</b></u><br /><br />Cancel before departure: Not Allowed<br />Cancel before departure - No Show: Not Allowed<br />Cancel after departure: Not Allowed<br />Cancel after departure - No Show: Not Allowed<br />Change before departure: Allowed with Restriction<br />Change before departure - No Show: Allowed with Restriction<br />Change after departure: Not Allowed<br />Change after departure - No Show: Not Allowed<br/> <br/><ul><li>GST, RAF AND ANY OTHER APPLICABLE CHARGES ARE EXTRA.</li><li>FEES ARE INDICATIVE PER PAX AND PER SECTOR.</li><li>FOR DOMESTIC BOOKINGS, PASSENGERS MUST SUBMIT THE CANCELLATION OR REISSUE REQUEST AT LEAST 2 HOURS BEFORE THE TIME LIMIT DEFINED IN THE AIRLINE's POLICY.</li><li>FOR INTERNATIONAL BOOKINGS, PASSENGERS MUST SUBMIT THE CANCELLATION OR REISSUE REQUEST AT LEAST 4 HOURS BEFORE THE TIME LIMIT DEFINED IN THE AIRLINE's POLICY.</li></ul>",
                        "FareRestriction": "",
                        "FareFamilyCode": "",
                        "FareRuleIndex": "",
                        "FareInclusions": []
                    }
                ],
                "MiniFareRules": [
                    {
                        "CFARExcludedDetails": null,
                        "JourneyPoints": "DEL-MAA",
                        "Type": "Reissue",
                        "From": "",
                        "To": "",
                        "Unit": "",
                        "Details": "INR 3000*",
                        "OnlineReissueAllowed": true,
                        "OnlineRefundAllowed": false
                    },
                    {
                        "CFARExcludedDetails": null,
                        "JourneyPoints": "DEL-MAA",
                        "Type": "Cancellation",
                        "From": "",
                        "To": "",
                        "Unit": "",
                        "Details": "INR 5000*",
                        "OnlineReissueAllowed": false,
                        "OnlineRefundAllowed": true
                    }
                ],
                "PenaltyCharges": {
                    "ReissueCharge": "",
                    "CancellationCharge": ""
                },
                "Status": 5,
                "Invoice": [
                    {
                        "CreditNoteGSTIN": null,
                        "GSTIN": null,
                        "InvoiceCreatedOn": "2026-03-10T16:49:56",
                        "InvoiceId": 52584,
                        "InvoiceNo": "DW/2526/52584",
                        "InvoiceAmount": 18310,
                        "Remarks": "",
                        "InvoiceStatus": 3
                    }
                ],
                "InvoiceAmount": 18310,
                "InvoiceNo": "DW/2526/52584",
                "InvoiceStatus": 3,
                "InvoiceCreatedOn": "2026-03-10T16:49:56",
                "Remarks": "",
                "IsWebCheckInAllowed": false
            },
            "Message": "",
            "TicketStatus": 1
        }
    }
}

#  LCC ticket request :

  {
"EndUserIp": "103.53.43.82",
"TokenId": "1e217420-9383-4699-bc1b-406e76bfd5d8",
"TraceId": "1f3a542c-8a4c-4ba7-a1dc-40eb04aafc53",
"ResultIndex": "OB6[TBO]yC1V7m2L/A3eehe7I74pQZbfDUrq6l/VL6I2lKo7SMpxft0QKV4svcQu7pX2dkBGyz2Yih5mS+uclf9m7uoXWCefoS4QzD8jQ4gpM+iqB315rXOHYB85fSFQnv1LYpkes+slZos2anEmMhm2M0rWIhzD2OcmC20eOuIzh4DPUvtToKyd7FWfhn02j0NZimC95gLtWl7rLcNF6R2ohKvRbW1GFMegjzc26PDihetkPL1WPy1YIOM7Lwb7xA5FF25x+/A5yf9AXcpldY8A1D7V4dvVCu8l/xWb1Bq59heJ7+AhtiQU5rO2Z0lrdQaQReSV08pRSqgCRuYjPvdHhvFJdmQNtTSLRdasx44kbDg8DxPBeU75/73smbZ4XR7YUHn56S+CoT7Ea6V0BgL37rAziWUlywkyl9xM7q+c/rJIWfVYRdL+NBxFVv97L2wRmrc5DfvgwJRTkq1vtmHaSWEtyCeFxaK+FQNNlfKxIzDlCTMbtKSZ1zHFHJoSKplvvsaQQRot9iQQaiMZn34oWFJWLil05VUKnFadY2OWh2jrn5usoI2/WpNVPHU80W50gtvcOifsfdkYIitpHitGwxO+zP2z6JAp8KUJ1wBuRshd20/eigkzI8hcrLbc5QTTe6z28EQ+2/Ex8YJCYLXiS11zKEZ6Tf4VRsA3pdXpw9Tl7cs=",
"Passengers": [
        {
            "Title": "Mr",
            "FirstName": "rahul",
            "LastName": "yadav",
            "PaxType": 1,
            "Gender": 1,
            "ContactNo": "1234567822",
            "Email": "harshdemotry@tbtasdvqert.in",
            "DateOfBirth": "1992-11-23T00:00:00",
            "IsLeadPax": true,
            "AddressLine1": "123, Test",
            "City": "Gurgaon",
            "CountryCode": "IN",
            "Fare": {
                "BaseFare": 1000,
                "Tax": 543,
                "YQTax": 0,
                "AdditionalTxnFeeOfrd": 0,
                "AdditionalTxnFeePub": 0,
                "PGCharge": 0
            },
            "Baggage": [
              {
                    "AirlineCode": "6E",
                    "FlightNumber": "176",
                    "WayType": 2,
                    "Code": "XBPE",
                    "Description": 2,
                    "Weight": 3,
                    "Currency": "INR",
                    "Price": 1950,
                    "Origin": "DEL",
                    "Destination": "BLR"
                }
            ],
            "MealDynamic": [
                {
                    "AirlineCode": "6E",
                    "FlightNumber": "176",
                    "WayType": 2,
                    "Code": "VBIR",
                    "Description": 2,
                    "AirlineDescription": "VEG BIRYANI Combo",
                    "Quantity": 1,
                    "Currency": "INR",
                    "Price": 400,
                    "Origin": "DEL",
                    "Destination": "BLR"
                }
            ],
            "SeatDynamic": [
             {
                                        "AirlineCode": "6E",
                                        "FlightNumber": "176",
                                        "CraftType": "A321-220",
                                        "Origin": "DEL",
                                        "Destination": "BLR",
                                        "AvailablityType": 1,
                                        "Description": 2,
                                        "Code": "16E",
                                        "RowNo": "16",
                                        "SeatNo": "E",
                                        "SeatType": 3,
                                        "SeatWayType": 2,
                                        "Compartment": 2,
                                        "Deck": 1,
                                        "Currency": "INR",
                                        "Price": 525
                                    }
            ]
        },
        {
            "Title": "Mr",
            "FirstName": "keshav",
            "LastName": "yadav",
            "PaxType": 2,
            "Gender": 1,
            "ContactNo": "1234567822",
            "Email": "harshdemotry@tbtasdvqert.in",
            "DateOfBirth": "2016-11-03T00:00:00",
            "IsLeadPax": false,
            "AddressLine1": "123, Test",
            "City": "Gurgaon",
            "CountryCode": "IN",
            "Fare": {
                "BaseFare": 1000,
                "Tax": 543,
                "YQTax": 0,
                "AdditionalTxnFeeOfrd": 0,
                "AdditionalTxnFeePub": 0,
                "PGCharge": 0
            },
            "MealDynamic": [
                {
                    "AirlineCode": "6E",
                    "FlightNumber": "176",
                    "WayType": 2,
                    "Code": "PTSW",
                    "Description": 2,
                    "AirlineDescription": "Paneer Tikka Sandwich Combo",
                    "Quantity": 1,
                    "Currency": "INR",
                    "Price": 500,
                    "Origin": "DEL",
                    "Destination": "BLR"
                }
            ],
            "SeatDynamic": [
               {
                                        "AirlineCode": "6E",
                                        "FlightNumber": "176",
                                        "CraftType": "A321-220",
                                        "Origin": "DEL",
                                        "Destination": "BLR",
                                        "AvailablityType": 1,
                                        "Description": 2,
                                        "Code": "16D",
                                        "RowNo": "16",
                                        "SeatNo": "D",
                                        "SeatType": 2,
                                        "SeatWayType": 2,
                                        "Compartment": 2,
                                        "Deck": 1,
                                        "Currency": "INR",
                                        "Price": 525
                                    }
            ]
        }
    ]
}
#  LCC ticket response :

{
    "Response": {
        "B2B2BStatus": false,
        "Error": {
            "ErrorCode": 0,
            "ErrorMessage": "",
        },
        "ResponseStatus": 1,
        "TraceId": "1f3a542c-8a4c-4ba7-a1dc-40eb04aafc53",
        "Response": {
            "ItineraryChangeList": null,
            "PNR": "CQ4FFC",
            "BookingId": 2090669,
            "SSRDenied": false,
            "SSRMessage": null,
            "Status": 1,
            "IsPriceChanged": false,
            "IsTimeChanged": false,
            "FlightItinerary": {
                "CommentDetails": null,
                "FareClassification": "Sale#Turquoise",
                "IsAutoReissuanceAllowed": true,
                "IsPartialVoidAllowed": true,
                "IsSeatsBooked": true, // what if false?
                "IssuancePcc": "OTI011",
                "JourneyType": 1,
                "SearchCombinationType": 2,
                "SupplierFareClasses": "Sale",
                "TBOConfNo": "TBFFCYA4V",
                "TBOTripID": null,
                "TripIndicator": 1,
                "BookingAllowedForRoamer": true,
                "BookingId": 2090669,
                "IsCouponAppilcable": true,
                "IsManual": false,
                "PNR": "CQ4FFC",
                "IsDomestic": true,
                "ResultFareType": "RegularFare",
                "Source": 6,
                "Origin": "DEL",
                "Destination": "BLR",
                "AirlineCode": "6E",
                "LastTicketDate": "2026-03-10T21:19:47",
                "ValidatingAirlineCode": "6E",
                "AirlineRemark": "6E main",
                "AirlineTollFreeNo": "1800-0001-5456-51515",
                "IsLCC": true,
                "NonRefundable": false,
                "FareType": "PUB",
                "CreditNoteNo": null,
                "Fare": {
                    "CFARAmount": 0,
                    "DCFARAmount": 0,
                    "ServiceFeeDisplayType": 0,
                    "Currency": "INR",
                    "BaseFare": 2000.0,
                    "Tax": 1086,
                    "TaxBreakup": [
                        {
                            "key": "K3",
                            "value": 0,
                        },
                        {
                            "key": "TotalTax",
                            "value": 1086.0,
                        },
                    ],
                    "YQTax": 0.0,
                    "AdditionalTxnFeeOfrd": 0,
                    "AdditionalTxnFeePub": 0.0,
                    "PGCharge": 0,
                    "OtherCharges": 0.0,
                    "ChargeBU": [
                        {
                            "key": "TBOMARKUP",
                            "value": 0,
                        },
                        {
                            "key": "GLOBALPROCUREMENTCHARGE",
                            "value": 0,
                        },
                        {
                            "key": "OTHERCHARGE",
                            "value": 0.0,
                        },
                        {
                            "key": "CONVENIENCECHARGE",
                            "value": 0,
                        },
                    ],
                    "Discount": 0.0,
                    "PublishedFare": 6986,
                    "CommissionEarned": 36.9,
                    "PLBEarned": 31.66,
                    "IncentiveEarned": 32.2,
                    "OfferedFare": 6925.54,
                    "TdsOnCommission": 14.76,
                    "TdsOnPLB": 12.66,
                    "TdsOnIncentive": 12.88,
                    "ServiceFee": 0,
                    "TotalBaggageCharges": 1950.0,
                    "TotalMealCharges": 900.0,
                    "TotalSeatCharges": 1050.0,
                    "TotalSpecialServiceCharges": 0.0,
                },
                "CreditNoteCreatedOn": null,
                "Passenger": [
                    {
                        "BarcodeDetails": {
                            "Id": 3370707,
                            "Barcode": [
                                {
                                    "Index": 1,
                                    "Format": "PDF417",
                                    "Content": "M1YADAV/RAHUL          CQ4FFC DELBLR6E 0176 077Y016E00000000",
                                    "BarCodeInBase64": null,
                                    "JourneyWayType": 3,
                                },
                            ],
                        },
                        "DocumentDetails": null,
                        "GuardianDetails": null,
                        "IsReissued": false,
                        "SegmentDetails": [
                            {
                                "CabinBaggage": {
                                    "FreeText": "7 Kg",
                                    "Unit": "Kg",
                                    "Value": "7",
                                },
                                "CheckedInBaggage": {
                                    "FreeText": "18 Kg",
                                    "Unit": "Kg",
                                    "Value": "18",
                                },
                                "FlightInfoIndex": "1",
                            },
                        ],
                        "PaxId": 3370707,
                        "Title": "Mr",
                        "FirstName": "rahul",
                        "LastName": "yadav",
                        "PaxType": 1,
                        "DateOfBirth": "1992-11-23T00:00:00",
                        "Gender": 1,
                        "IsPANRequired": false,
                        "IsPassportRequired": false,
                        "PAN": "",
                        "PassportNo": "",
                        "AddressLine1": "123, Test",
                        "Fare": {
                            "CFARAmount": 0,
                            "DCFARAmount": 0,
                            "ServiceFeeDisplayType": 0,
                            "Currency": "INR",
                            "BaseFare": 1000.0,
                            "Tax": 543,
                            "TaxBreakup": [
                                {
                                    "key": "K3",
                                    "value": 0,
                                },
                                {
                                    "key": "TotalTax",
                                    "value": 543.0,
                                },
                            ],
                            "YQTax": 0.0,
                            "AdditionalTxnFeeOfrd": 0,
                            "AdditionalTxnFeePub": 0.0,
                            "PGCharge": 0,
                            "OtherCharges": 0.0,
                            "ChargeBU": [
                                {
                                    "key": "TBOMARKUP",
                                    "value": 0,
                                },
                                {
                                    "key": "GLOBALPROCUREMENTCHARGE",
                                    "value": 0,
                                },
                                {
                                    "key": "OTHERCHARGE",
                                    "value": 0.0,
                                },
                                {
                                    "key": "CONVENIENCECHARGE",
                                    "value": 0,
                                },
                            ],
                            "Discount": 0.0,
                            "PublishedFare": 4418,
                            // PublishedFare = BaseFare + Tax + TotalBaggageCharges + TotalMealCharges + TotalSeatCharges + TotalSpecialServiceCharges
                            "CommissionEarned": 18.45,
                            "PLBEarned": 15.83,
                            "IncentiveEarned": 16.1,
                            "OfferedFare": 4387.77,
                            "TdsOnCommission": 7.38,
                            "TdsOnPLB": 6.33,
                            "TdsOnIncentive": 6.44,
                            "ServiceFee": 0,
                            "TotalBaggageCharges": 1950.0,
                            "TotalMealCharges": 400.0,
                            "TotalSeatCharges": 525.0,
                            "TotalSpecialServiceCharges": 0.0,
                        },
                        "City": "Gurgaon",
                        "CountryCode": "IN",
                        "Nationality": "IN",
                        "ContactNo": "1234567822",
                        "Email": "harshdemotry@tbtasdvqert.in",
                        "IsLeadPax": true,
                        "FFAirlineCode": null,
                        "FFNumber": null,
                        "Baggage": [
                            {
                                "AirlineCode": "6E",
                                "FlightNumber": "176",
                                "WayType": 2,
                                "Code": "XBPE",
                                "Description": 2,
                                "Weight": 3,
                                "Currency": "INR",
                                "Price": 1950.0,
                                "Origin": "DEL",
                                "Destination": "BLR",
                            },
                        ],
                        "MealDynamic": [
                            {
                                "AirlineCode": "6E",
                                "FlightNumber": "176",
                                "WayType": 2,
                                "Code": "VBIR",
                                "Description": 2,
                                "AirlineDescription": "VEG BIRYANI Combo",
                                "Quantity": 1,
                                "Currency": "INR",
                                "Price": 400.0,
                                "Origin": "DEL",
                                "Destination": "BLR",
                            },
                        ],
                        "SeatDynamic": [
                            {
                                "AirlineCode": "6E",
                                "FlightNumber": "176",
                                "CraftType": "A321-220",
                                "Origin": "DEL",
                                "Destination": "BLR",
                                "AvailablityType": 1,
                                "Description": 2,
                                "Code": "16E",
                                "RowNo": "16",
                                "SeatNo": "E",
                                "SeatType": 3,
                                "SeatWayType": 2,
                                "Compartment": 2,
                                "Deck": 1,
                                "Currency": "INR",
                                "Price": 525.0,
                            },
                        ],
                        "Ssr": [],
                        "Ticket": {
                            "TicketId": 2382085,
                            "TicketNumber": "CQ4FFC",
                            "IssueDate": "2026-03-10T15:24:49",
                            "ValidatingAirline": "708",
                            "Remarks": "",
                            "ServiceFeeDisplayType": "ShowInTax",
                            "Status": "OK",
                            "ConjunctionNumber": "",
                            "TicketType": "N",
                        },
                        "SegmentAdditionalInfo": [
                            {
                                "FareBasis": "S0IP",
                                "NVA": "",
                                "NVB": "",
                                "Baggage": "18 Kg|3",
                                "Meal": "1 Platter",
                                "Seat": "16E",
                                "SpecialService": "",
                                "CabinBaggage": "7 Kg",
                            },
                        ],
                    },
                    {
                        "BarcodeDetails": {
                            "Id": 3370708,
                            "Barcode": [
                                {
                                    "Index": 1,
                                    "Format": "PDF417",
                                    "Content": "M1YADAV/KESHAV         CQ4FFC DELBLR6E 0176 077Y016D00000000",
                                    "BarCodeInBase64": null,
                                    "JourneyWayType": 3,
                                },
                            ],
                        },
                        "DocumentDetails": null,
                        "GuardianDetails": null,
                        "IsReissued": false,
                        "SegmentDetails": [
                            {
                                "CabinBaggage": {
                                    "FreeText": "7 Kg",
                                    "Unit": "Kg",
                                    "Value": "7",
                                },
                                "CheckedInBaggage": {
                                    "FreeText": "15 Kg",
                                    "Unit": "Kg",
                                    "Value": "15",
                                },
                                "FlightInfoIndex": "1",
                            },
                        ],
                        "PaxId": 3370708,
                        "Title": "Mr",
                        "FirstName": "keshav",
                        "LastName": "yadav",
                        "PaxType": 2,
                        "DateOfBirth": "2016-11-03T00:00:00",
                        "Gender": 1,
                        "IsPANRequired": false,
                        "IsPassportRequired": false,
                        "PAN": "",
                        "PassportNo": "",
                        "AddressLine1": "123, Test",
                        "Fare": {
                            "CFARAmount": 0,
                            "DCFARAmount": 0,
                            "ServiceFeeDisplayType": 0,
                            "Currency": "INR",
                            "BaseFare": 1000.0,
                            "Tax": 543,
                            "TaxBreakup": [
                                {
                                    "key": "K3",
                                    "value": 0,
                                },
                                {
                                    "key": "TotalTax",
                                    "value": 543.0,
                                },
                            ],
                            "YQTax": 0.0,
                            "AdditionalTxnFeeOfrd": 0,
                            "AdditionalTxnFeePub": 0.0,
                            "PGCharge": 0,
                            "OtherCharges": 0.0,
                            "ChargeBU": [
                                {
                                    "key": "TBOMARKUP",
                                    "value": 0,
                                },
                                {
                                    "key": "GLOBALPROCUREMENTCHARGE",
                                    "value": 0,
                                },
                                {
                                    "key": "OTHERCHARGE",
                                    "value": 0.0,
                                },
                                {
                                    "key": "CONVENIENCECHARGE",
                                    "value": 0,
                                },
                            ],
                            "Discount": 0.0,
                            "PublishedFare": 2568,
                            "CommissionEarned": 18.45,
                            "PLBEarned": 15.83,
                            "IncentiveEarned": 16.1,
                            "OfferedFare": 2537.77,
                            "TdsOnCommission": 7.38,
                            "TdsOnPLB": 6.33,
                            "TdsOnIncentive": 6.44,
                            "ServiceFee": 0,
                            "TotalBaggageCharges": 0.0,
                            "TotalMealCharges": 500.0,
                            "TotalSeatCharges": 525.0,
                            "TotalSpecialServiceCharges": 0.0,
                        },
                        "City": "Gurgaon",
                        "CountryCode": "IN",
                        "Nationality": "IN",
                        "ContactNo": "1234567822",
                        "Email": "harshdemotry@tbtasdvqert.in",
                        "IsLeadPax": true,
                        "FFAirlineCode": null,
                        "FFNumber": null,
                        "Baggage": [
                            {
                                "AirlineCode": "6E",
                                "FlightNumber": "176",
                                "WayType": 2,
                                "Code": "NoBaggage",
                                "Description": 2,
                                "Weight": 0,
                                "Currency": "INR",
                                "Price": 0.0,
                                "Origin": "DEL",
                                "Destination": "BLR",
                            },
                        ],
                        "MealDynamic": [
                            {
                                "AirlineCode": "6E",
                                "FlightNumber": "176",
                                "WayType": 2,
                                "Code": "PTSW",
                                "Description": 2,
                                "AirlineDescription": "Paneer Tikka Sandwich Combo",
                                "Quantity": 1,
                                "Currency": "INR",
                                "Price": 500.0,
                                "Origin": "DEL",
                                "Destination": "BLR",
                            },
                        ],
                        "SeatDynamic": [
                            {
                                "AirlineCode": "6E",
                                "FlightNumber": "176",
                                "CraftType": "A321-220",
                                "Origin": "DEL",
                                "Destination": "BLR",
                                "AvailablityType": 1,
                                "Description": 2,
                                "Code": "16D",
                                "RowNo": "16",
                                "SeatNo": "D",
                                "SeatType": 2,
                                "SeatWayType": 2,
                                "Compartment": 2,
                                "Deck": 1,
                                "Currency": "INR",
                                "Price": 525.0,
                            },
                        ],
                        "Ssr": [],
                        "Ticket": {
                            "TicketId": 2382086,
                            "TicketNumber": "CQ4FFC",
                            "IssueDate": "2026-03-10T15:24:49",
                            "ValidatingAirline": "708",
                            "Remarks": "",
                            "ServiceFeeDisplayType": "ShowInTax",
                            "Status": "OK",
                            "ConjunctionNumber": "",
                            "TicketType": "N",
                        },
                        "SegmentAdditionalInfo": [
                            {
                                "FareBasis": "S0IP",
                                "NVA": "",
                                "NVB": "",
                                "Baggage": "15 Kg",
                                "Meal": "1 Platter",
                                "Seat": "16D",
                                "SpecialService": "",
                                "CabinBaggage": "7 Kg",
                            },
                        ],
                    },
                ],
                "CancellationCharges": null,
                "Segments": [
                    {
                        "Baggage": "15 Kilograms",
                        "CabinBaggage": "7 KG ",
                        "CabinClass": 2,
                        "SupplierFareClass": null,
                        "TripIndicator": 1,
                        "SegmentIndicator": 1,
                        "Airline": {
                            "AirlineCode": "6E",
                            "AirlineName": "IndiGo",
                            "FlightNumber": "176",
                            "FareClass": "SS",
                            "OperatingCarrier": "",
                        },
                        "AirlinePNR": "",
                        "Origin": {
                            "Airport": {
                                "AirportCode": "DEL",
                                "AirportName": "Indira Gandhi Airport",
                                "Terminal": "1",
                                "CityCode": "DEL",
                                "CityName": "Delhi",
                                "CountryCode": "IN",
                                "CountryName": "India",
                            },
                            "DepTime": "2026-03-18T14:20:00",
                        },
                        "Destination": {
                            "Airport": {
                                "AirportCode": "BLR",
                                "AirportName": "Kempegowda International Airport",
                                "Terminal": "1",
                                "CityCode": "BLR",
                                "CityName": "Bangalore",
                                "CountryCode": "IN",
                                "CountryName": "India",
                            },
                            "ArrTime": "2026-03-18T17:10:00",
                        },
                        "Duration": 170,
                        "GroundTime": 0,
                        "Mile": 0,
                        "StopOver": false,
                        "FlightInfoIndex": "1",
                        "StopPoint": "",
                        "StopPointArrivalTime": "0001-01-01T00:00:00",
                        "StopPointDepartureTime": "0001-01-01T00:00:00",
                        "Craft": "321",
                        "Remark": "Sale",
                        "IsETicketEligible": true,
                        "FlightStatus": "Confirmed",
                        "Status": "HK",
                        "FareClassification": {
                            "Color": "Turquoise",
                            "Type": "Sale",
                        },
                    },
                ],
                "FareRules": [
                    {
                        "Origin": "DEL",
                        "Destination": "BLR",
                        "Airline": "6E",
                        "FareBasisCode": "S0IP",
                        "FareRuleDetail": "The FareBasisCode is: S0IP<br />These are Fare Rules for Domestic Flights.<ul><li>Meal: Chargable.</li><li>Seat: Chargable.</li><li> HandBag: 1 Bag Upto 7 Kg.</li><li>Check-in Baggage: 15 Kg.</li><li>Check-in Baggage (Student Fare): 25 Kg.</li></ul><table border=\"1\"><tr><td rowspan=\"4\">Change fee <br /><b>(Fare Difference is also applicable)</b></td></tr><tr><td>No. of Days Left For Departure</td><td>Domestic</td></tr><tr><td>0-3 (DAYS)</td><td>INR 2999</td></tr><tr><td>4 DAYS AND ABOVE</td><td>INR 2250</td></tr><tr><td rowspan=\"4\">Cancellation Fee<br/ ><b>or Airfare charges (Whichever is lower)</b></td></tr><tr><td>No. of Days Left For Departure</td><td>Domestic</td></tr><tr><td>0-3 (DAYS)</td><td>INR 3999</td></tr><tr><td>4 DAYS AND ABOVE</td><td>INR 2999</td></tr></table><br />Subject to change without prior notice. <b>Note</b> : We should receive the request at least four hours prior to Airline Fare Rules Policy.\r\n<br/> <br/><ul><li>GST, RAF AND ANY OTHER APPLICABLE CHARGES ARE EXTRA.</li><li>FEES ARE INDICATIVE PER PAX AND PER SECTOR.</li><li>FOR DOMESTIC BOOKINGS, PASSENGERS MUST SUBMIT THE CANCELLATION OR REISSUE REQUEST AT LEAST 2 HOURS BEFORE THE TIME LIMIT DEFINED IN THE AIRLINE's POLICY.</li><li>FOR INTERNATIONAL BOOKINGS, PASSENGERS MUST SUBMIT THE CANCELLATION OR REISSUE REQUEST AT LEAST 4 HOURS BEFORE THE TIME LIMIT DEFINED IN THE AIRLINE's POLICY.</li></ul>",
                        "FareRestriction": null,
                        "FareInclusions": [
                            "Cabin Baggage - 07KG",
                            "Check-In baggage - 15KG",
                            "Cancellation fees - Applicable",
                            "Reissue fees - Applicable",
                            "Seat - Chargeable",
                            "Meal - Chargeable\t",
                        ],
                    },
                ],
                "MiniFareRules": [
                    {
                        "CFARExcludedDetails": null,
                        "JourneyPoints": "",
                        "Type": "",
                        "From": "",
                        "To": "",
                        "Unit": "",
                        "Details": "",
                        "OnlineReissueAllowed": false,
                        "OnlineRefundAllowed": false,
                    },
                ],
                "PenaltyCharges": {},
                "Status": 5,
                "Invoice": [
                    {
                        "CreditNoteGSTIN": null,
                        "GSTIN": null,
                        "InvoiceCreatedOn": "2026-03-10T15:24:49",
                        "InvoiceId": 52551,
                        "InvoiceNo": "DW/2526/52551",
                        "InvoiceAmount": 6926.0,
                        "Remarks": "",
                        "InvoiceStatus": 3,
                    },
                ],
                "InvoiceAmount": 6926.0,
                "InvoiceNo": "DW/2526/52551",
                "InvoiceStatus": 3,
                "InvoiceCreatedOn": "2026-03-10T15:24:49",
                "Remarks": "",
                "IsWebCheckInAllowed": false,
            },
            "TicketStatus": 1,
        },
    },
}



