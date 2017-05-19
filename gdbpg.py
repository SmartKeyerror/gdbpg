import gdb

PlanNodes = ['Result', 'Repeat', 'Append', 'Sequence', 'Motion', 'AOCSScan',
        'BitmapAnd', 'BitmapOr', 'Scan', 'SeqScan', 'TableScan',
        'IndexScan', 'DynamicIndexScan', 'BitmapIndexScan',
        'BitmapHeapScan', 'BitmapAppendOnlyScan', 'BitmapTableScan',
        'DynamicTableScan', 'TidScan', 'SubqueryScan', 'FunctionScan',
        'TableFunctionScan', 'ValuesScan', 'ExternalScan', 'AppendOnlyScan',
        'Join', 'NestLoop', 'MergeJoin', 'HashJoin', 'ShareInputScan',
        'Material', 'Sort', 'Agg', 'Window', 'Unique', 'Hash', 'SetOp',
                'Limit', 'DML', 'SplitUpdate', 'AssertOp', 'RowTrigger',
                'PartitionSelector' ]

def format_plan_tree(tree, indent=0):
    'formats a plan (sub)tree, with custom indentation'

    # if the pointer is NULL, just return (null) string
    if (str(tree) == '0x0'):
        return '-> (NULL)'

    retval = '''
-> %(type)s (cost=%(startup).3f...%(total).3f rows=%(rows)s width=%(width)s) id=%(plan_node_id)s
\ttarget list:
%(target)s''' % {
        'type': format_type(tree['type']),    # type of the Node
        'startup': float(tree['startup_cost']),    # startup cost
        'total': float(tree['total_cost']),    # total cost
        'rows': str(tree['plan_rows']),    # number of rows
        'width': str(tree['plan_width']),    # tuple width (no header)
        'plan_node_id': str(tree['plan_node_id']),

        # format target list
        'target': format_node_list(tree['targetlist'], 2, True)
        }

    if (str(tree['qual']) != '0x0'):
        retval +='''
\tqual:
%(qual)s''' % {
            'qual': format_node_list(tree['qual'], 2, True)
        }

    if is_a(tree, 'HashJoin') or is_a(tree, 'Join'):
        join = cast(tree, 'Join')
        retval+='''
\t joinqual:
%(joinqual)s''' % {
            'joinqual': format_node_list(join['joinqual'], 2, True)
        }

    if is_a(tree, 'Append'):
        append = cast(tree, 'Append')
        retval += '''
\t%(appendplans)s''' % {
        # format Append subplans
        'appendplans': format_appendplan_list(append['appendplans'], 0)
        }
    elif is_a(tree, 'SubqueryScan'):
        subquery = cast(tree, 'SubqueryScan')
        retval += '''
\t%(subplan)s''' % {
        'subplan': format_plan_tree(subquery['subplan'], 0)
        }
    else:
    # format all the important fields (similarly to EXPLAIN)
        retval +='''
\t%(left)s
\t%(right)s''' % {

        # left subtree
        'left': format_plan_tree(tree['lefttree'], 0),

        # right subtree
        'right': format_plan_tree(tree['righttree'], 0)
        }

    return add_indent(retval, indent + 1)

def format_query_info(node, indent=0):
    'formats a query node with custom indentation'
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = '''          type: %(type)s
  command type: %(commandType)s
  query source: %(querySource)s
   can set tag: %(canSetTag)s
   range table:
%(rtable)s
      jointree: %(jointree)s
''' % {
        'type': format_type(node['type']),
        'commandType': format_type(node['commandType']),
        'querySource': format_type(node['querySource']),
        'canSetTag': (int(node['canSetTag']) == 1),
        'rtable': format_node_list(node['rtable'], 1, True),
        'jointree': format_node(node['jointree']),
      }

    return retval

def format_appendplan_list(lst, indent):
    retval = format_node_list(lst, indent, True)
    return add_indent(retval, indent + 1)

def format_type(t, indent=0):
    'strip the leading T_ from the node type tag'

    t = str(t)

    if t.startswith('T_'):
        t = t[2:]

    return add_indent(t, indent)


def format_int_list(lst, indent=0):
    'format list containing integer values directly (not warapped in Node)'

    # handle NULL pointer (for List we return NIL
    if (str(lst) == '0x0'):
        return '(NIL)'

    # we'll collect the formatted items into a Python list
    tlist = []
    item = lst['head']

    # walk the list until we reach the last item
    while str(item) != '0x0':

        # get item from the list and just grab 'int_value as int'
        tlist.append(int(item['data']['int_value']))

        # next item
        item = item['next']

    return add_indent(str(tlist), indent)


def format_oid_list(lst, indent=0):
    'format list containing Oid values directly (not warapped in Node)'

    # handle NULL pointer (for List we return NIL)
    if (str(lst) == '0x0'):
        return '(NIL)'

    # we'll collect the formatted items into a Python list
    tlist = []
    item = lst['head']

    # walk the list until we reach the last item
    while str(item) != '0x0':

        # get item from the list and just grab 'oid_value as int'
        tlist.append(int(item['data']['oid_value']))

        # next item
        item = item['next']

    return add_indent(str(tlist), indent)


def format_node_list(lst, indent=0, newline=False):
    'format list containing Node values'

    # handle NULL pointer (for List we return NIL)
    if (str(lst) == '0x0'):
        return '(NIL)'

    # we'll collect the formatted items into a Python list
    tlist = []
    item = lst['head']

    # walk the list until we reach the last item
    while str(item) != '0x0':

        # we assume the list contains Node instances, so grab a reference
        # and cast it to (Node*)
        node = cast(item['data']['ptr_value'], 'Node')

        # append the formatted Node to the result list
        tlist.append(format_node(node))

        # next item
        item = item['next']

    retval = str(tlist)
    if newline:
        retval = "\n".join([str(t) for t in tlist])

    return add_indent(retval, indent)


def format_char(value):
    '''convert the 'value' into a single-character string (ugly, maybe there's a better way'''

    str_val = str(value.cast(gdb.lookup_type('char')))

    # remove the quotes (start/end)
    return str_val.split(' ')[1][1:-1]


def format_relids(relids):
    return '(not implemented)'


def format_node_array(array, start_idx, length, indent=0):

    items = []
    for i in range(start_idx, start_idx + length - 1):
        items.append(str(i) + " => " + format_node(array[i]))

    return add_indent(("\n".join(items)), indent)


def format_node(node, indent=0):
    'format a single Node instance (only selected Node types supported)'

    if str(node) == '0x0':
        return add_indent('(NULL)', indent)

    retval = ''
    type_str = str(node['type'])

    if is_a(node, 'TargetEntry'):

        # we assume the list contains Node instances (probably safe for Plan fields)
        node = cast(node, 'TargetEntry')

        name_ptr = node['resname'].cast(gdb.lookup_type('char').pointer())
        name = "(NULL)"
        if str(name_ptr) != '0x0':
            name = '"' + (name_ptr.string()) + '"'

        retval = 'TargetEntry (resno=%(resno)s resname=%(name)s origtbl=%(tbl)s origcol=%(col)s junk=%(junk)s expr=[%(expr)s])' % {
            'resno': node['resno'],
            'name': name,
            'tbl': node['resorigtbl'],
            'col': node['resorigcol'],
            'junk': (int(node['resjunk']) == 1),
            'expr': format_node(node['expr'])
        }

    elif is_a(node, 'Var'):

        # we assume the list contains Node instances (probably safe for Plan fields)
        node = cast(node, 'Var')

        retval = 'Var (varno=%(no)s varattno=%(attno)s levelsup=%(levelsup)s)' % {
            'no': node['varno'],
            'attno': node['varattno'],
            'levelsup': node['varlevelsup']
        }

    elif is_a(node, 'Aggref'):
        node = cast(node, 'Aggref')

        retval = '''Aggref (aggfnoid=%(fnoid)s aggtype=%(aggtype)s aggstage=%(stage)s)
\tAggref Args:
%(args)s''' % {
            'fnoid': node['aggfnoid'],
            'aggtype': node['aggtype'],
            'stage': node['aggstage'],
            'args': format_node_list(node['args'], 2, True)
        }

    elif is_a(node, 'CaseExpr'):
        node = cast(node, 'CaseExpr')

        retval = '''CaseExpr (casetype=%(casetype)s defresult=%(defresult)s arg=%(arg)s)
\tCaseExpr Args:
%(args)s''' % {
            'casetype': node['casetype'],
            'defresult': format_node(node['defresult']),
            'arg': format_node(node['arg']),
            'args': format_node_list(node['args'], 2, True)
        }

    elif is_a(node, 'CaseWhen'):
        node = cast(node, 'CaseWhen')

        retval = '''CaseWhen (expr=%(expr)s result=%(result)s)''' % {
                'expr': format_node(node['expr']),
                'result': format_node(node['result'])
        }


    elif is_a(node, 'RangeTblRef'):

        node = cast(node, 'RangeTblRef')

        retval = 'RangeTblRef (rtindex=%d)' % (int(node['rtindex']), )

    elif is_a(node, 'RelOptInfo'):

        node = cast(node, 'RelOptInfo')

        retval = 'RelOptInfo (kind=%(kind)s relids=%(relids)s rtekind=%(rtekind)s relid=%(relid)s rows=%(rows)s width=%(width)s fk=%(fk)s)' % {
            'kind': node['reloptkind'],
            'rows': node['rows'],
            'width': node['width'],
            'relid': node['relid'],
            'relids': format_relids(node['relids']),
            'rtekind': node['rtekind'],
            'fk': (int(node['has_fk_join']) == 1)
        }

    elif is_a(node, 'RangeTblEntry'):

        node = cast(node, 'RangeTblEntry')

        retval = 'RangeTblEntry (kind=%(rtekind)s relid=%(relid)s)' % {
            'relid': node['relid'],
            'rtekind': node['rtekind']
    #'relkind' : format_char(node['relkind'])
        }

    elif is_a(node, 'GenericExprState'):

        node = cast(node, 'GenericExprState')
        retval = format_generic_expr_state(node)

    elif is_a(node, 'PlannerInfo'):

        retval = format_planner_info(node)

    elif is_a(node, 'PlannedStmt'):

        retval = format_planned_stmt(node)

    elif is_a(node, 'List'):

        retval = format_node_list(node, 0, True)

    elif is_a(node, 'Plan'):

        retval = format_plan_tree(node)

    elif is_a(node, 'RestrictInfo'):

        node = cast(node, 'RestrictInfo')

        retval = '''RestrictInfo (pushed_down=%(push_down)s can_join=%(can_join)s delayed=%(delayed)s)
%(clause)s
%(orclause)s''' % {
            'clause': format_node(node['clause'], 1),
            'orclause': format_node(node['orclause'], 1),
            'push_down': (int(node['is_pushed_down']) == 1),
            'can_join': (int(node['can_join']) == 1),
            'delayed': (int(node['outerjoin_delayed']) == 1)
        }

    elif is_a(node, 'OpExpr'):

        node = cast(node, 'OpExpr')

        retval = format_op_expr(node)

    elif is_a(node, 'BoolExpr'):

        node = cast(node, 'BoolExpr')

        print(node)

        retval = format_bool_expr(node)

    elif is_a(node, 'Query'):

        retval = format_query_info(node)

    elif is_plannode(node):
        node = cast(node, 'Plan')
        retval = format_plan_tree(node)

    else:
        # default - just print the type name
        retval = format_type(type_str)

    return add_indent(str(retval), indent)

def is_plannode(node):
    for nodestring in PlanNodes:
        if is_a(node, nodestring):
            return True

    return False

def format_planner_info(info, indent=0):

    # Query *parse;			/* the Query being planned */
    # *glob;				/* global info for current planner run */
    # Index	query_level;	/* 1 at the outermost Query */
    # struct PlannerInfo *parent_root;	/* NULL at outermost Query */
    # List	   *plan_params;	/* list of PlannerParamItems, see below */

    retval = '''rel:
%(rel)s
rte:
%(rte)s
''' % {
        'rel':
        format_node_array(info['simple_rel_array'], 1,
                          int(info['simple_rel_array_size'])),
        'rte':
        format_node_array(info['simple_rte_array'], 1,
                          int(info['simple_rel_array_size']))
    }

    return add_indent(retval, indent)


def format_planned_stmt(plan, indent=0):

    retval = '''          type: %(type)s
       planGen: %(planGen)s
   can set tag: %(can_set_tag)s
     transient: %(transient)s
               
     plan tree: %(tree)s
   range table:
%(rtable)s
 relation OIDs: %(relation_oids)s
   result rels: %(result_rels)s
  utility stmt: %(util_stmt)s
      subplans: %(subplans)s''' % {
        'type': plan['commandType'],
        'planGen': plan['planGen'],
    #'qid' : plan['queryId'],
    #'nparam' : plan['nParamExec'],
    #'has_returning' : (int(plan['hasReturning']) == 1),
    #'has_modify_cte' : (int(plan['hasModifyingCTE']) == 1),
        'can_set_tag': (int(plan['canSetTag']) == 1),
        'transient': (int(plan['transientPlan']) == 1),
    #'row_security' : (int(plan['hasRowSecurity']) == 1),
        'tree': format_plan_tree(plan['planTree']),
        'rtable': format_node_list(plan['rtable'], 1, True),
        'relation_oids': format_oid_list(plan['relationOids']),
        'result_rels': format_int_list(plan['resultRelations']),
        'util_stmt': format_node(plan['utilityStmt']),
        'subplans': format_node_list(plan['subplans'], 1, True)
    }

    return add_indent(retval, indent)

def format_generic_expr_state(node, indent=0):
    exprstate = node['xprstate']
    child = cast(node['arg'], 'ExprState')
    return '''GenericExprState [evalFunc=%(evalFunc)s childEvalFunc= %(childEvalFunc)s]
\t%(expr)s''' % {
#\tChild Expr:
#%(childexpr)s''' % {
            'expr': format_node(exprstate['expr']),
            'evalFunc': format_node(exprstate['evalfunc']),
            'childexpr': format_node(child['expr']),
            'childEvalFunc': child['evalfunc']
    }


def format_op_expr(node, indent=0):

    return """OpExpr [opno=%(opno)s opfuncid=%(opfuncid)s opresulttype=%(opresulttype)s]
%(clauses)s""" % {
        'opno': node['opno'],
        'opfuncid': node['opfuncid'],
        'opresulttype': node['opresulttype'],
        'clauses': format_node_list(node['args'], 1, True)
    }


def format_bool_expr(node, indent=0):

    return """BoolExpr [op=%(op)s]
%(clauses)s""" % {
        'op': node['boolop'],
        'clauses': format_node_list(node['args'], 1, True)
    }


def is_a(n, t):
    '''checks that the node has type 't' (just like IsA() macro)'''

    if not is_node(n):
        return False

    return (str(n['type']) == ('T_' + t))


def is_node(l):
    '''return True if the value looks like a Node (has 'type' field)'''

    try:
        x = l['type']
        return True
    except:
        return False


def cast(node, type_name):
    '''wrap the gdb cast to proper node type'''

    # lookup the type with name 'type_name' and cast the node to it
    t = gdb.lookup_type(type_name)
    return node.cast(t.pointer())


def add_indent(val, indent):

    return "\n".join([(("\t" * indent) + l) for l in val.split("\n")])


class PgPrintCommand(gdb.Command):
    "print PostgreSQL structures"

    def __init__(self):
        super(PgPrintCommand, self).__init__("pgprint", gdb.COMMAND_SUPPORT,
                                             gdb.COMPLETE_NONE, False)

    def invoke(self, arg, from_tty):

        arg_list = gdb.string_to_argv(arg)
        if len(arg_list) != 1:
            print("usage: pgprint var")
            return

        l = gdb.parse_and_eval(arg_list[0])

        if not is_node(l):
            print("not a node type")

        print(format_node(l))


PgPrintCommand()
