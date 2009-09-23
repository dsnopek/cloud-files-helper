#!/usr/bin/env python
# Chmouel Boudjnah <chmouel.boudjnah@rackspace.co.uk>
import os
import sys

from optparse import OptionParser

import cloudfiles

USERNAME = "RCLOUD_API_USER" in os.environ and \
    os.environ["RCLOUD_API_USER"] or raw_input("Username: ")
API_KEY = "RCLOUD_API_KEY" in os.environ and \
    os.environ["RCLOUD_API_KEY"] or raw_input("API Key: ")
CONNEXION = None

def format_bytes(bytes, precision=2):
    labels = (
            (1<<40L, 'TiB'),
            (1<<30L, 'GiB'),
            (1<<20L, 'MiB'),
            (1<<10L, 'KiB'),
            (1, 'bytes')
            )
    if bytes == 1:
        return (1, 'byte')
    for factor, label in labels:
        if not bytes >= factor:
            continue
        float_split = str(bytes/float(factor)).split('.')
        integer = float_split[0]
        decimal = float_split[1]
        if int(decimal[0:precision]):
            float_string = '.'.join([integer, decimal[0:precision]])
        else:
            float_string = integer
            return (float_string, label)

def choose_container():
    containers = CONNEXION.list_containers()
    if not containers:
        print "nothing, nada, niet, rien!"
        sys.exit(1)
    for i in xrange(len(containers)):
        print "%d) %s" % (i + 1, containers[i])
    print "Choose container: ",
    num = int(raw_input())

    if num > len(containers):
        print "Invalid answer"
        sys.exit(1)
    return containers[num - 1]

def choose_object(container):
    objects = container.list_objects()
    for i in xrange(len(objects)):
        print "%d) %s" % (i + 1, objects[i])
    print "Choose Object: ",
    num = int(raw_input())

    if num > len(objects):
        print "Invalid answer"
        sys.exit(1)
    return objects[num - 1]

def cf_ls():
    ls_options = OptionParser(usage="ls [OPTION] [container]")
    (options, args) = ls_options.parse_args()
    
    if len(args) > 1:
        ls_options.print_help()
        sys.exit(0)
    
    if not args:
        print "Listing Containers:"
        for container in sorted(CONNEXION.list_containers()):
            print container
        return
    else:
        container = args[0]
            
    try:
        cnt = CONNEXION.get_container(container)
    except(cloudfiles.errors.NoSuchContainer):
        print "No such container: %s" % container
        sys.exit(1)

    print
    print "Listing container: %s" % container
    objects = cnt.list_objects()
    if not objects:
        print "No files in '%s'" % container
        return
    banner_string = "%-30s %-30s %-30s" % ("Name", "Size", "Type")
    print banner_string
    print "-" * len(banner_string)
    total_size = 0
    for obj in sorted(objects):
        obj = cnt.get_object(obj)
        if obj.size:
            size = obj.size
            total_size += obj.size
        print "%-30s %-30s %-30s" % \
            (obj.name, "".join(format_bytes(size)), obj.content_type)
    print
    print "Total: Size: %s Objects: %d" % \
        ("".join(format_bytes(total_size)), len(objects))
        
def cf_rm():
    rm_options = OptionParser(usage="rm [OPTION] container[/file]")
    rm_options.add_option('-r', '--recursive',
                          action="store_true",
                          default=False,
                          help="Recursive delete for container.")
    (options, args) = rm_options.parse_args()
    if not args:
        rm_options.print_help()
        sys.exit(0)
    
    recursive = options.recursive
    if not "/" in args[0]:
        container = args[0]

        if recursive:
            container = CONNEXION.get_container(container)
            for obj in container.list_objects():
                print "Deleting %s/%s" % (container, obj)
                container.delete_object(obj)
        try:
            CONNEXION.delete_container(container)
        except(cloudfiles.errors.ContainerNotEmpty):
            print "ERROR: Container %s not empty..." % container
        else:
            print "Container %s deleted." % container
        return
    else:
        container, obj = args[0].split("/")
        container = CONNEXION.get_container(container)        
        container.delete_object(obj)
        
def cf_cp():
    dest = "./"
    epilog = """by default it will copy the file to the current
directory unless [dest] is specified. Only one way for now (from
remote to local) and one file only."""
    cp_options = OptionParser(usage="cp container/file [dest]", \
                                  epilog=epilog)
    (options, args) = cp_options.parse_args()
    
    if len(args) >= 1:
        if len(args) == 2:
            dest = args[1]
        container, obj = args[0].split("/")
        container = CONNEXION.get_container(container)
    else:
        container = CONNEXION.get_container(choose_container())
        obj = choose_object(container)

    obj = container.get_object(obj)
    obj.save_to_filename(os.path.join(dest, str(obj)))
    
if __name__ == '__main__':
    try:
        CONNEXION = cloudfiles.get_connection(USERNAME, API_KEY)
    except(cloudfiles.errors.AuthenticationFailed):
        print "Error: Username or API Key is invalid."
        sys.exit(1)
        
    base_name = os.path.basename(sys.argv[0])
    if base_name == "cp":
        cf_cp()
    elif base_name == "rm":
        cf_rm()
    elif base_name == "ls":
        cf_ls()     
