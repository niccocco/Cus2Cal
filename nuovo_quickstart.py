from __future__ import print_function

import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify', "https://www.googleapis.com/auth/calendar"]


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)

        #prendo tutte le mail del cus non lette
        query = "from:info@cusfirenze.it is:unread"
        results = service.users().messages().list(userId='me', q=query).execute()
        labels = results.get("messages", {})
        print(labels)
        if not labels:
            print('No labels found.')
            return
        print('Labels:')
        i=0
        for label in labels:
            #per ciascuna mail, leggo il contenuto
            id = label["id"]
            i +=1
            lettura = build("gmail", "v1", credentials=creds)

            risultato = lettura.users().messages().get(userId="me", id=id).execute()
            #miao = open("risultato" + str(i) + ".json", "w+")
            #miao.write(str(risultato["payload"]["parts"]))
            #miao.close()

            #cerco quale elemento contiene il corpo della mail in base64
            corpo = risultato["payload"]["parts"]
            for c in corpo:
                if c["mimeType"] == "text/plain":
                    #decodifico da base64
                    base64_bytes = c["body"]["data"].encode("iso-8859-1")
                    message_bytes = base64.b64decode(base64_bytes)
                    message = message_bytes.decode("iso-8859-1")

                    #print(message)

                    if "hai prenotato" in message:
                        #prendo il nome della prenotazione
                        prenotazione = message.partition("hai prenotato ")[2]
                        nome = prenotazione.partition(" ")[0]

                        prenotazione = prenotazione.partition("(codice ")[2]
                        codice = prenotazione.partition(")")[0]

                        prenotazione = prenotazione.partition("per il giorno ")[2]
                        giorno = prenotazione.partition("\r")[0]

                        prenotazione = prenotazione.partition("dalle ")[2]
                        ora_inizio = prenotazione.partition(" ")[0]

                        prenotazione = prenotazione.partition("alle ")[2]
                        ora_fine = prenotazione.partition(".\r")[0]

                        prenotazione = prenotazione.partition("Numero prenotazione: ")[2]
                        numero_prenotazione = prenotazione.partition("\r")[0]
                        print(nome, codice, giorno, ora_inizio, ora_fine, numero_prenotazione)


                        miao = {"timezone":"Europe/Rome"}

                        #creo il json dell'evento
                        evento = {
                            "summary": "Prenotazione CUS {}".format(nome),
                            "description":"Codice: {}, Numero prenotazione: {}".format(codice,numero_prenotazione),
                            "start": {
                                "dateTime": data_form(giorno,ora_inizio),
                                "timeZone": "Europe/Rome"
                            },
                            "end": {
                                "dateTime": data_form(giorno, ora_fine),
                                "timeZone": "Europe/Rome"
                            },
                        }

                        try:
                            service = build('calendar', 'v3', credentials=creds)
                            event = service.events().insert(calendarId='primary', body=evento).execute()
                            print ('Event created: %s' % (event.get('htmlLink')))

                            #segno la mail come letta
                            rimuovi_lettura = {
                                "removeLabelIds": [
                                    "UNREAD",
                                    "INBOX"
                                    ]
                            }
                            risultato = lettura.users().messages().modify(userId= "me", id =id, body=rimuovi_lettura).execute()
                            print("Email segnata come letta con successo")
                        except HttpError as error:
                                print('An error occurred: %s' % error)

                        #                  



    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


def data_form(giorno,orario) -> str:
    d, m, a = giorno.split("/")
    ora, mi = orario.split(":")
    secondi = 00
    return "{}-{}-{}T{}:{}:{}".format(a,m,d,ora,mi,secondi)


#la data è nel formato aaaa-mm-dd:
miao = {"timezone":"Europe/Rome"}

if __name__ == '__main__':
    main()