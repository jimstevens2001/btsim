import sys

def distance_parse(type, out_file, arg1, arg2):
    if type == 'node':
        file = 'distance_record'
        f = open(file, 'r')
        of = open(out_file, 'w')
        node = arg
        if arg2 != 0:
            style = arg2
            copy = 0
            time = '0'
            for line in f:
                if line != '/n':
                    # text description line
                    if len(line) > 15:
                        if line.find(str(node)) != -1:
                            copy = 1
                            time = line[44]
                            i = 45
                            while line[i] != ' ':
                                time = time+line[i]
                                i = i+1
                            if style == 'times_only':
                                of.write(time+'/n')
                    # measurement line
                    elif copy == 1 and len(line) > 1:
                        if style == 'values_only':
                            of.write(line)
                        copy = 0
        else:
            copy = 0
            for line in f:
                if line != '/n':
                    # text description line
                    if len(line) > 15:
                        if line.find(str(node)) != -1:
                            copy = 1
                    # measurement line
                    elif copy == 1 and len(line) > 1:
                        of.write(line)
                        copy = 0
        f.close()
        of.close()
    #average
    elif type == 'time':
        file = 'distance_record'
        style = arg1
        f = open(file, 'r')
        of = open(out_file, 'w')
            
        num = 0
        average = 0
        time = '0'
        for line in f:
            if line != '/n' and line != ' ':
                #text description line
                if len(line) > 15:
                    if line.find(time) != -1:
                        pass
                    else:
                        average = average/num
                        if style == 'times_only':
                            of.write(time+'\n')
                        elif style == 'averages_only':
                            of.write(str(average)+'\n')
                        else:
                            of.write(time+' : '+str(average)+'\n')
                        average = 0
                        num = 0
                        time = line[44]
                        i = 45
                        while line[i] != ' ':
                            time = time+line[i]
                            i = i+1
                elif len(line) > 1:
                    average = average + float(line)
                    num = num+1
        f.close()
        of.close()


if sys.argv[1] == 'distance_record':
     if len(sys.argv) > 2:
        if sys.argv[2] == '-node':
            node = sys.argv[3]
            if len(sys.argv) > 4:
                style = sys.argv[4]
                if style == 'times_only':
                    out_file = 'distance_times_only'
                else:
                    out_file = str(node)+'_distance'
                type = 'node'
                distance_parse(type, out_file, node, style)
            else:
                out_file = str(node)+'_distance'
                type = 'node'
                distance_parse(type, out_file, node, 0)
            
        elif sys.argv[2] == '-time':
            style = sys.argv[3]
            if style == 'times_only':
                out_file = 'distance_times_only'
            elif style == 'averages_only':
                out_file = 'distance_averages_only'
            else:
                out_file = 'time_distance'
            type = 'time'
            distance_parse(type, out_file, style, 0)
     else:
         print 'incorrect formatting \n'
    
else:
    print 'Please enter a valid input file \n'
    print 'Currently supported output files: \n'
    print '    - distance_record \n'
    print 'Exiting'
