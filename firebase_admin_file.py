from firebase_admin import credentials, firestore, initialize_app, messaging
from google.cloud.firestore_v1.base_query import FieldFilter, BaseCompositeFilter
from datetime import datetime, timezone, timedelta

creds = credentials.Certificate('/home/luke/Desktop/Script/Credentials/solar-logger.json')
initialize_app(creds)

db = firestore.client()



def send_notification(msg_topic, msg_title, msg_body):
    """
    Android app notifications.
    """
    message = messaging.Message(
    notification=messaging.Notification(
    title=msg_title,
    body =msg_body,),
    topic=msg_topic,)
    response = messaging.send(message)
    return


def write_line(date_time_utc, new_line_data, lastHourDocumentRef, readingObj):
    lastHourDocumentRef = update_hour_document(db.transaction(), date_time_utc, new_line_data, lastHourDocumentRef, readingObj, collection_name="test")    
    return lastHourDocumentRef
    

# Run a transaction to store data
@firestore.transactional
def update_hour_document(transaction, date_time_utc, new_line_data, lastHourDocumentRef, readingObj, collection_name):
    """
    -------------------------------------------------------
    Appends a single line to the current hour document.
    Tracks daily max for two important temperatures.
    Creates new doc if it does not exist.
    -------------------------------------------------------
    """
    collection_ref = db.collection(collection_name)
    # Construct
    conditions = [['hour', '>=', date_time_utc], ['hour', '<=', date_time_utc + timedelta(seconds=1)]]
    query = collection_ref.where(filter=BaseCompositeFilter('AND', [FieldFilter(*_c) for _c in conditions]))
    
    # Execute
    documents = query.get()

    # Check if the document exists
    if len(list(documents)) > 0:
        #print(f"Document with timestamp {date_time_utc} exists. {documents[0].id}")
        # Get document reference and data
        doc_ref = documents[0].reference
        doc_data = documents[0].to_dict()
        # Add the new line
        max_glycol_in = doc_data.get('glycol_in_max', 0.01)

        max_glycol_in = max([readingObj.glycol_in, max_glycol_in])
        max_glycol_roof = doc_data.get('glycol_roof_max', 0.01)
        max_glycol_roof = max([readingObj.glycol_in_roof, max_glycol_roof])
        lines = doc_data.get('lines', [])
        lines.append(new_line_data)
        # Update within the transaction
        transaction.update(doc_ref, {'lines': lines})
        transaction.update(doc_ref, {'last_reading': datetime.now(timezone.utc)})
        transaction.update(doc_ref, {'glycol_in_max': max_glycol_in})
        transaction.update(doc_ref, {'glycol_roof_max': max_glycol_roof})
        # if the hour has changed use the previous document id to compress that hour

    else:
        #print(f"Document with timestamp {date_time_utc} does not exist. creating document")
        # creating new hour doc with knowledge of previous hour doc (get max and min, then compress)
        if lastHourDocumentRef is not None:
            prev_doc_snapshot = lastHourDocumentRef.get()
            prev_doc_data = prev_doc_snapshot.to_dict()
            max_glycol_in = prev_doc_data.get('glycol_in_max', 0.01)
            max_glycol_roof = prev_doc_data.get('glycol_roof_max', 0.01)
        # creating new doc without knowledge of previous hour doc (set max and min)
        else:
            max_glycol_in = 0.01
            max_glycol_roof = 0.01
            log_event(f"new doc created with No previous doc Id in memory  {max_glycol_in} {max_glycol_roof} need to locate last max.  Some crash occured.")
            #getLastKnownMax()
        
        # reset the min and max daily at this hour
        if datetime.now().hour == 5:
            max_glycol_in = 0.01
            max_glycol_roof = 0.01
        
        new_doc_data = {
            'hour': date_time_utc,
            'lines': [new_line_data],
            'glycol_in_max': max_glycol_in,
            'glycol_roof_max': max_glycol_roof,
            'last_reading': datetime.now(timezone.utc)}
        # Insert new document
        doc_ref = collection_ref.add(new_doc_data)[1]
        
        # Since this hours doc does not exist. it is a new hour. compress the previous hour.
        compress_previous_hour(collection_ref, date_time_utc, lastHourDocumentRef)
        
    return doc_ref


def compress_previous_hour(collection_ref, date_time_utc, previousHourDocumentRef):
    """
    -------------------------------------------------------
    Compress the last hour (if it exists) when a new document is created.
    If no doc ref in memory, query the db to find the previous doc.
    -------------------------------------------------------
    """
    doc_data = None
    if previousHourDocumentRef is None:
        # Construct
        conditions = [['hour', '>=', date_time_utc - timedelta(hours=1)], ['hour', '<=', date_time_utc - timedelta(hours=1) + timedelta(seconds=1)]]
        query = collection_ref.where(filter=BaseCompositeFilter('AND', [FieldFilter(*_c) for _c in conditions]))
        # Execute
        documents = query.get()

        # Check if the document exists. we dont know the reference. maybe system rebooted.       
        if len(list(documents)) > 0:
            previousHourDocumentRef = documents[0].reference
            doc_data = documents[0].to_dict()
        # Else nothing to compress.
        else:
            log_event(f"previousDocumentRef is None and query returned no results for {date_time_utc} nothing to compress")
    
    else: # we already know the previous hours doc reference.        
        doc_data = previousHourDocumentRef.get().to_dict()

    if doc_data is not None:
        # Compress lines  Avg, max, min
        output_line = compress_doc_data(previousHourDocumentRef, doc_data)
        doc_ref = update_week_document(db.transaction(), date_time_utc, output_line, collection_name="weeks")
        delete_old_documents(date_time_utc, collection_name='test')

    return 
        
def compress_doc_data(previousHourDocumentRef, doc_data):
    """
    -------------------------------------------------------
    Calculates averages, maximums, and minimums for each sensor.
    Called when a new hourly document is created.
    -------------------------------------------------------
    """    
    #hour = doc_data.get('hour')
    lines = doc_data.get('lines', [])

    averages = []
    average_counts = []
    maximums = []
    minimums = []

    firstLine = True
    for line in lines:
        line = line.split(",")
        i = 1
        while i < len(line):
            try:
                value = float(line[i])
                if firstLine:
                    averages.append(value)
                    average_counts.append(1)
                    maximums.append(value) 
                    minimums.append(value)
                else:
                    averages[i-1] += value
                    average_counts[i-1] += 1
                    maximums[i-1] = max(maximums[i-1], value)
                    minimums[i-1] = min(minimums[i-1], value)
            except:
                # value is None. Append 0 if the list is empty.
                # this could be improved
                if firstLine:
                    averages.append(0)
                    average_counts.append(1)
                    maximums.append(0) 
                    minimums.append(0)
                else:
                    pass
            i += 1
        firstLine = False

    # calculate averages
    i -= 1
    k = 0
    while k < len(averages):
        # +0.001 rounds the .005 up
        averages[k] = round(averages[k]/average_counts[k]+0.001,2)
        k += 1

    # format results  
    time = datetime.now() - timedelta(hours=1)
    output_line = ""  
    output_line += (f"{time.strftime('%Y-%m-%d %H:%M:%S')},")
    output_line += ",".join(f"{avg},{maxm},{minm}" for avg, maxm, minm in zip(averages, maximums, minimums))
    with open("Output/averageDebug.csv", 'a') as file:        
        file.write(output_line + "\n")
    file.close()

    return output_line

@firestore.transactional
def update_week_document(transaction, date_time_utc, new_line_data, collection_name):
    """
    -------------------------------------------------------
    Appends a single compressed line of avg, max, min for each sensor into the current weeks document.
    Called when a new hourly document is created. Used to show a weekly summary.
    Creates new doc if it does not exist.
    -------------------------------------------------------
    """ 
    collection_ref = db.collection(collection_name)
    # Construct
    week_no = date_time_utc.isocalendar().week
    year = date_time_utc.isocalendar().year
    #conditions = [['_week_number', '>=', week_no], ['_week_number', '<=', week_no ]]
    conditions = [['_week_number', '==', week_no], ['_year', '==', year ]]
    query = collection_ref.where(filter=BaseCompositeFilter('AND', [FieldFilter(*_c) for _c in conditions]))
    
    # Execute
    documents = query.get()

    # Check if the document exists
    if len(list(documents)) > 0:
        #print(f"Document with timestamp {date_time_utc} exists. {documents[0].id}")
        # Get document reference and data
        doc_ref = documents[0].reference
        doc_data = documents[0].to_dict()
        # Add the new line
        lines = doc_data.get('lines', [])
        lines.append(new_line_data)
        # Update within the transaction
        transaction.update(doc_ref, {'lines': lines})
        transaction.update(doc_ref, {'last_reading': datetime.now(timezone.utc)})    
    else:
        #print(f"Document with timestamp {date_time_utc} does not exist. creating document")
        new_doc_data = {
            '_week_number': week_no,
            '_year': year,
            'lines': [new_line_data],
            'last_reading': datetime.now(timezone.utc)}
        # Insert new document
        doc_ref = collection_ref.add(new_doc_data)[1]

    return doc_ref

def delete_old_documents(date_time_utc, collection_name):
    """
    -------------------------------------------------------
    Removes hourly documents that are older than one week.
    No need for more than one week of detailed info on firebase.
    -------------------------------------------------------
    """ 
    collection_ref = db.collection(collection_name)
    conditions = [['hour', '<=', date_time_utc - timedelta(weeks=1)]]
    query = collection_ref.where(filter=BaseCompositeFilter('AND', [FieldFilter(*_c) for _c in conditions]))

    docs = query.stream()

    for doc in docs:
        doc.reference.delete()
    return

def log_event(message):
    """
    -------------------------------------------------------
    Writes a message to file.
    Includes Datetime.
    Use: log_event("errors.txt", "my error")
    -------------------------------------------------------
    """ 
    with open("/home/luke/Desktop/Script/Logs/errors_firebase_admin_file.txt", 'a') as output_file:
        output_file.write(f"{str(datetime.now())}  {message}\n")
    output_file.close()
    return
    
