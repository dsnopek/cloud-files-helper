#!/usr/bin/env python
#Hacky
import cloudfiles
import os,sys

username="RCLOUD_API_USER" in os.environ and os.environ["RCLOUD_API_USER"] or raw_input("Username: ")
api_key="RCLOUD_API_KEY" in os.environ and os.environ["RCLOUD_API_KEY"] or raw_input("API Key: ")

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
        
def rm(cnx, rm_container=False, recursive=False):
    if rm_container:
        if len(sys.argv) > 1:
            container=sys.argv[1]
        else:
            container = choose_container(cnx)

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

    if len(sys.argv) > 1:
        container,obj=sys.argv[1].split("/")
        container = cnx.get_container(container)
    else:
        container = cnx.get_container(choose_container(cnx))
        obj = choose_object(cnx, container)
        
    print dir(container)
        
def cp(cnx, rm_container=False, recursive=False):
    if len(sys.argv) > 1:
        container,obj=sys.argv[1].split("/")
        container = cnx.get_container(container)
    else:
        container = cnx.get_container(choose_container(cnx))
        obj = choose_object(cnx, container)

    obj = container.get_object(obj)
    obj.save_to_filename(str(obj))
    
if __name__ == '__main__':
    try:
        cnx = cloudfiles.get_connection(username, api_key)
    except(cloudfiles.errors.AuthenticationFailed):
        print "Error: Username or API Key is invalid."
        sys.exit(1)
        
    name = os.path.basename(sys.argv[0])
    if name == "cp":
        cp(cnx)
    elif name == "rm":
        rm_container=False
        recursive=False
        if '-c' in sys.argv:
            sys.argv.remove('-c')
            rm_container=True
            if '-r' in sys.argv:
                recursive=True
                sys.argv.remove('-r')
        
        rm(cnx, rm_container=rm_container, recursive=recursive)
    elif name == "ls":
        just_container=False
        if '-c' in sys.argv:
            sys.argv.remove('-c')
            just_container=True

        ls(cnx, just_container=just_container)     
