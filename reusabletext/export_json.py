import parse
import ctprep
import codecs
import json

def export_selected_orct(selectfile, globalErrors=()):
    'export JSON for ORCT in a lecture'
    tree = parse.process_select(selectfile)
    ctstem = selectfile.split('.')[0]
    outfile = ctstem + '.json'
    print 'writing', outfile
    data = tree.list_repr(textFunc=ctprep.flag_rst_images,
                            postprocDict=parse.PostprocDict)
    with codecs.open(outfile, 'w', encoding='utf-8') as ofile:
        json.dump(data, ofile)


## def get_node_dict(node, textFunc=ctprep.flag_rst_images,
##                   postprocDict=parse.PostprocDict):
##     'get dict of metadata attr and child nodes'
##     d = dict(text=textFunc(node.text))
##     if node.tokens[0].startswith(':'):
##         d['kind'] = node.tokens[0][1:-1]
##     else:
##         d['kind'] = node.tokens[0]
##     if getattr(node, 'title', ''):
##         d['title'] = node.title
##     if len(node.tokens) >= 2 and node.tokens[1]:
##         d['rustID'] = node.tokens[1]
##     d.update(node.metadata_dict())
##     for k, v in node.child_dict(postprocDict=postprocDict).items():
##         d[k] = [textFunc(text) for text in v]
##     return d

    
    
if __name__ == '__main__':
    import sys
    export_selected_orct(*sys.argv[1:])
