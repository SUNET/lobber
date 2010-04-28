def valid_ace_p(ace):
    """Return True if ACE is a valid access control entry, otherwise
    False.

    BUG: We don't allow '.' and potential other characters needed.
    """
    entl, _, perm = ace.partition('#')
    if not entl or not perm:
        return False
    if not entl.replace(':', '').replace('_', '').isalnum():
        return False
    if len(perm) > 1:
        return False
    if not perm in 'rwd':
        return False
    return True        
