import sys
import os

def encrypt(key, msg):
    """
    Encrypts a message using a simple Caesar cipher.

    Parameters:
    - key (str): The encryption key.
    - msg (str): The message to be encrypted.

    Returns:
    - str: The encrypted message.
    """
    encrypted = []
    for i, c in enumerate(msg):
        key_c = ord(key[i % len(key)])
        msg_c = ord(c)
        encrypted.append(chr((msg_c + key_c) % 127))
    return ''.join(encrypted)

def main():
    """
    Main function to take user input, encrypt the Oracle DB password, and print the results.
    """
    # Get the current working directory
    pwd = os.getcwd()

    # Prompt the user for the Oracle DB password
    msg = raw_input("Please enter the Oracle DB password to be encrypted: ")

    # Check if the entered password is empty
    if msg == "":
       print("Please provide a valid password as input.")
       sys.exit()

    # Encryption key for the Caesar cipher
    key = "password encryption"

    # Encrypt the password
    encrypted = encrypt(key, msg)

    # Print the original and encrypted passwords
    print('Password To Be Encrypted:', str(msg))
    print('Encrypted:', str(encrypted))
    print("Please keep this password in config.ini file along with special characters.")

if __name__ == '__main__':
    main()
