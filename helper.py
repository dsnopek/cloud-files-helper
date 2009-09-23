#!/usr/bin/env python
# Chmouel Boudjnah <chmouel.boudjnah@rackspace.co.uk>
import os
import sys

from optparse import OptionParser

import cloudfiles

USERNAME="RCLOUD_API_USER" in os.environ and os.environ["RCLOUD_API_USER"] or raw_input("Username: ")
API_KEY="RCLOUD_API_KEY" in os.environ and os.environ["RCLOUD_API_KEY"] or raw_input("API Key: ")

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

def choose_container(cnx):
    containers = cnx.list_containers()
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

def choose_object(cnx, container):
    objects = container.list_objects()
    for i in xrange(len(objects)):
        print "%d) %s" % (i + 1, objects[i])
    print "Choose Object: ",
    num = int(raw_input())

    if num > len(objects):
        print "Invalid answer"
        sys.exit(1)
    return objects[num - 1]

def ls(cnx, just_container=False):
    if just_container:
        for container in sorted(cnx.list_containers()):
            print container
        return
    if len(sys.argv) > 1:
        container=sys.argv[1]
    else:
        container = choose_container(cnx)
        print
        print "Listing container: %s" % container
    try:
        cnt = cnx.get_container(container)
    except(cloudfiles.errors.NoSuchContainer):
        print "No such container: %s" % container
        sys.exit(1)
    objects=cnt.list_objects()
    if not objects:
        print "No files in '%s'" % container
        return
    s="%-30s %-30s %-30s" % ("Name", "Size", "Type")
    print s
    print "-" * len(s)
    total_size=0
    for obj in sorted(objects):
        o=cnt.get_object(obj)
        if o.size:
            size=o.size
            total_size += o.size
        print "%-30s %-30s %-30s" % (o.name, "".join(format_bytes(size)), o.content_type)
    print "Total: Size: %s Objects: %d" % ("".join(format_bytes(total_size)), len(objects))
        
def rm(cnx, rm_container=False):
    cp_options = OptionParser(usage="rm [OPTION] container[/file]")
    cp_options.add_option('-r', '--recursive', action="store_true", default=False, help="Recursive delete for container.")
    (options, args) = cp_options.parse_args()
    if not args:
        cp_options.print_help()
        sys.exit(0)
    
    recursive = options.recursive
    if not "/" in args[0]:
        container=args[0]

        if recursive:
            container = cnx.get_container(container)
            for obj in container.list_objects():
                print "Deleting %s/%s" % (container, obj)
                container.delete_object(obj)
        try:
            cnx.delete_container(container)
        except(cloudfiles.errors.ContainerNotEmpty):
            print "ERROR: Container %s not empty..." % container
        else:
            print "Container %s deleted." % container
        return
    else:
        container,obj=args[0].split("/")
        container = cnx.get_container(container)        
        container.delete_object(obj)
        
def cp(cnx, rm_container=False, recursive=False):
    dest="./"
    epilog="""by default it will copy the file to the current
directory unless [dest] is specified. Only one way for now (from
remote to local) and one file only."""
    cp_options = OptionParser(usage="cp container/file [dest]", \
                                  epilog=epilog)
    (options, args) = cp_options.parse_args()
    
    if len(args) >= 1:
        if len(args) == 2:
            dest = args[1]
        container,obj=args[0].split("/")
        container = cnx.get_container(container)
    else:
        container = cnx.get_container(choose_container(cnx))
        obj = choose_object(cnx, container)

    obj = container.get_object(obj)
    obj.save_to_filename(os.path.join(dest, str(obj)))
    
if __name__ == '__main__':
    try:
        cnx = cloudfiles.get_connection(USERNAME, API_KEY)
    except(cloudfiles.errors.AuthenticationFailed):
        print "Error: Username or API Key is invalid."
        sys.exit(1)
        
    name = os.path.basename(sys.argv[0])
    if name == "cp":
        cp(cnx)
    elif name == "rm":
        rm(cnx)
    elif name == "ls":
        just_container=False
        if '-c' in sys.argv:
            sys.argv.remove('-c')
            just_container=True

        ls(cnx, just_container=just_container)     
