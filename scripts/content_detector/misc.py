def string_to_float(string, log=True, item_string=None, do_correct=True):
    """Return float from string.

    Arguments:
        string (str): string to convert to float
        log (bool): set whether to print log messages (default True)
        item_string (str): string to be printed with error message (default None)
        do_correct (bool): set whether to ask user for correct values (default
            True)

    Returns:
        float if conversion was successful, False otherwise

    """

    def get_correct_value():
        """Get a correct value for quantity or price from user."""
        while True:
            user_input = input('\nEnter a valid number: ')
            try:
                float_user_input = float(user_input)
            except ValueError:
                print('Wrong input! Try again.')
            else:
                return float_user_input

    try:
        value = float(string)
    except ValueError as e:
        if log:
            # Print log messages
            if item_string:
                print(f'\nError occurred for item: "{item_string}"')
            print(e)

        if do_correct:
            # Interactively get correct the value
            value = get_correct_value()
        else:
            value = False
    finally:
        return value
