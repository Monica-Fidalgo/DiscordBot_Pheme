from datetime import datetime

def birthday():
    '''
    Returns a birthday message if today is a discor user's birthday.
            
            Returns: 
                    msg_list (list): List of strings with birthday message(s).
    '''
    # Dictionary with user's birthday information
    bdays = [
        ("Burn",'24/07',228494443668439040),
        ("Momo",'20/11',233955951323906048),
        ("Sukoi",'06/09',234424901157650432),
        ("BlueRaven",'06/11',233993911624794123),
        ("Daniel",'29/06',243214755785867264),
        ("Coarse",'17/04',319503417783615498)
    ]

    # Check today's date
    now = datetime.now() 
    today = now.strftime('%d/%m')

    msg_list = []

    # If today's date corresponds to a birthday date, send a birthday message
    for user,date,id in bdays:
        if date == today:    
            msg = 'Happy Birthday, '+ user +'!'
            msg_list.append(msg)
    
    return msg_list