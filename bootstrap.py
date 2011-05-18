#!/usr/bin/python 

"""A holder file as we don't need a bootstrap but this CI configs to be more generic."""

import os

def main():
    """Create a fake bin dir with a dummy buildout script."""

    try:
        os.mkdir('bin')
    except OSError:
        pass
        
    f = open('bin/buildout', 'w')
    f.write("""#!/usr/bin/python
pass""")
    f.close()
    
    os.chmod('bin/buildout', 0755)

if __name__ == "__main__":
    main()

