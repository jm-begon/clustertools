# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
This example illustrates how to retrieve experiment results
"""
import sys

from clustertools.database import load_results

__COLWIDTH__ = 10

def nicefy(s, width=__COLWIDTH__):
    s = str(s)
    if len(s) > width:
        return s[:width]
    else:
        pad = (width - len(s))
        left_pad = pad //2
        right_pad = pad - left_pad
        return " "*left_pad + s +" "*right_pad



if __name__ == "__main__":
    # Get the name of the experiment
    exp_name = "basic"
    if len(sys.argv) > 1:
        exp_name = sys.argv[1]

    # Load the results
    results = load_results(exp_name)

    if len(results) == 0:
        print("No result")
        sys.exit()

    # Display the results
    print("="*50)
    print("Experiment: '"+exp_name+"'")
    print("="*50)

    r0 = results[results.keys()[0]]



    parameters = r0["Parameters"].keys()
    metrics = r0["Results"].keys()

    for i, m in enumerate(metrics):
        print("Metric", i, ":", str(m), "")
        print("~"*37)


        template = " {} |"*len(parameters)
        template += "| {} || {}"

        title_template = [nicefy(p) for p in parameters]
        title_template.append((nicefy(m)))
        title_template.append("Computation name")
        title = template.format(*title_template)

        print(title)
        print("-"*len(title))


        for comp_name, info in results.items():
            params = info["Parameters"]
            row_template = [nicefy(params[p]) for p in parameters]
            row_template.append(nicefy(info["Results"][m]))
            row_template.append(comp_name)
            print(template.format(*row_template))

        print()




