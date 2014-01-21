
# In[1]:

# Modified Stylesheet for notebook.
from IPython.core.display import HTML
def css_styling():
    styles = open("custom.css", "r").read()
    return HTML(styles)

css_styling()


# Out[1]:

#     <IPython.core.display.HTML at 0x2e48210>

# #Change Detection Tutorial
# ##Some Scaffolding
# 
# 
#  * Offline vs. Online change detection
#  * We write some utility functions that allow us to 
#   * pass signals to a change detection algorithm in "online" simulation mode
#   * calculate residuals after receiving each new data point
#   * Test the stopping rules at each iteration
#   * Plot results and output conveniently.
# 

# In[4]:

get_ipython().magic(u'matplotlib')
import matplotlib.pyplot as plt
import numpy as np


# Out[4]:

#     Using matplotlib backend: module://IPython.kernel.zmq.pylab.backend_inline
# 

# In[5]:

from collections import defaultdict
np.random.seed(seed=111111)
np.set_printoptions(precision=3, suppress=True)


# ## Aside: Offline vs. Online algorithms
# 
# An "offline" change detection algorithm is one in which we are given the entire signal and are attempting to "look back" and recognize where the change occcured. 
# 
# An "online" algorithm is quite different, in which we imagine our signal as "streaming into" our detector, and at any given moment we only have knowledge of the most recent data point and whatever information we chose to retain about the history of the signal. 
# 
# Reference: Sequential Analysis http://en.wikipedia.org/wiki/Sequential_analysis
# 
# My interest is in the latter "online" class of algorithms. That means I want to make sure data points are passed to the algorithm one by one, and that I am interested in 
# 
#   1. detecting a change, 
#   2. in deciding whether a change is significant enough to trigger an alert, and 
#   3. in how quickly I can detect the change after it occurs. 
# 
# I also want to make sure that I am not cheating when I run my experiments. 
# 
# To do all this, it is helpful to write some code that helps me simulate the online streaming scenario of interest. 

# ## Thus we need some Scaffolding
# 
# 
# I want to be able to realistically simulate streaming data for my online algorithm experiments. That is, I want to write code that simulates a scenario in which 
# 
#  * each data point is passed to the algorithm one by one
#  * the algorithm performs its analysis on that new information along with any stored historical information
#  * the algorithm decides after each data point whether or not a change has been detected. 
# 
# The following code will provide this framework and enable us to run some experiments more conveniently. Feel free to skip this section. 
# 
# 

# An online simulation function might look something like this: 
# ----------------------
# (pseudocode)
# 
# function online_simulator(signal, cd_algorithm, stopping rules): 
#   
#   Iterate through the signal, passing data points to the algorithm. FOR EACH data point
#     Calculate residuals
#     Compare residuals with the stopping rule(s)
#     IF the stopping rule is triggered
#       RETURN (True, residuals, stopping_rule_triggered)
# 
#   At the end of the signal, IF the stopping rule is not triggered
#      THEN return (False, residuals)
# 

# I am not clear on 'Essentially the algorithm is just calculating residuals and updating them for each new value passed.'
#  -- [Blaine]

# What about the change detection algorithm, what does that look like? 
# 
# Essentially the algorithm is just calculating residuals and updating them for each new value passed. 
# -------------------------
# (pseudocode)
# 
# class cd_algorithm:
#    Initialization
#       initialize residuals
# 
#    METHOD step FOR EACH new_signal_value
#       Update residuals
#       Check if Stopping Rules have been triggered
#       IF rules_triggered
#         RETURN (True, residuals, signal_size, stopping_rule_triggered)
#       
# ----
# actually we'll make that step method into a generator, so we can yield values for each new value of the signal.

# In[6]:

def dict_to_arrays(ddict):
    """
    Convenience function used by online simulator to bundle 
    residuals into a dict before returning
    """
    new_dict = {}
    for k,v in ddict.iteritems():
        new_dict[k] = np.array(v)
    return new_dict


# In[7]:

def online_simulator(signal, change_detector): 
    """
    Function that simulates an online streaming scenario for change detection experiments.
    --- 
    Given a signal and a change detector, this simulator passes one signal data point at a time to
    the change detector and processes the results. 
    """
    #Initiate
    #change_detector = cd_algorithm()
    
    all_residuals = defaultdict(list)
    
    xx = 0
    #Iterate through the signal, passing data points to the algorithm. 
    for value in signal: 
        
        #calculate residuals, compare residuals with the stopping rule(s)
        check_results = next(change_detector.step(value))
        
        #process results
        rule_triggered    = check_results[0]
        res               = check_results[1]
        
        #store residuals
        for k,v in res.iteritems():
            all_residuals[k].append(v)
              
        if rule_triggered == True: 
            #stopping rule was triggered          
            return (True, dict_to_arrays(all_residuals))    

    #Rule wasn't triggered by end of signal
    return (False, dict_to_arrays(all_residuals))


# What is the type/object of the signal that is being iterated over?
# -- [Blaine]

# In[8]:

def run_online_simulation(signal, change_detector, scale=True): 
    """Run simulation and print results"""
    
    #Run simulation
    results = online_simulator(signal, change_detector)
    
    #Display results
    print_sim_results(signal, results, scale=scale)
    
    #Return residuals
    residuals = results[1]
    return residuals


# In[9]:

class change_detector(object):
    """
    A change detection algorithm. 
    
    The algorithm calculates residuals and updates them for each new value passed. 
    Residuals are checked against stopping rules at each change, yielding either True or False, accordingly. 
    
    """
    
    def __init__(self): 
        #Interim and calculated values
        self.signal_size = 0
        self.total_val = 0
        
        self.mean_ = np.nan
    
    def update_residuals(self, new_signal_value): 
        #Update residuals
        self.signal_size += 1
        self.total_val += new_signal_value
        self.mean_ = self.total_val / self.signal_size
    
    def _get_residual_dict(self): 
        """create a dictionary of residuals to return. 
        Inclues all class and instance variables ending in '_'
        """
        residuals_dict = {}
        for k,v in self.__dict__.iteritems():
            if k.endswith('_'):
                residuals_dict[k] = v
        
        return residuals_dict
        
    def check_stopping_rules(self, new_signal_value): 
        rules_triggered = False
        
        #No rules implemented
        pass
        
        return rules_triggered
    
    def _step(self, new_signal_value): 
        
        #update residuals
        self.update_residuals(new_signal_value)
        
        ## compare residuals to stopping_rules
        rules_triggered = self.check_stopping_rules(new_signal_value)
        
        if rules_triggered: 
            yield (True, self._get_residual_dict())
        
        else: 
            yield (False, self._get_residual_dict())
      
    def step(self, new_signal_value):
        return self._step(new_signal_value)


# In[10]:

def print_sim_results(signal, results, **kwargs):
    """
    Another convenience function to print out the results of our experiment. 
    """
    #Get results
    stopped = results[0]
    residuals = results[1]
    print "Residuals: {}".format([res for res in residuals.viewkeys()])

    if stopped: 
        #length of residuals array tells us when the rule was triggered
        stop_point = len(residuals.itervalues().next())
          
        print "Change detected. Stopping Rule triggered at {}.\n".format(stop_point)
        plot_signal_and_residuals(signal, residuals, stop_point, **kwargs)
    else: 
        print "Stopping rule not triggered."
        plot_signal_and_residuals(signal, residuals, **kwargs)


# In[11]:

def plot_signal_and_residuals(signal, residuals=None, stop_point=None, scale=True):
    """Convenience function to generate plots of the signal and the residuals"""
    
    if residuals is None:
        plotcount = 1
    else: 
        plotcount = 1 + len(residuals)
    
    fig, axes = plt.subplots(nrows=plotcount, 
                             ncols = 1, 
                             sharex=True,
                             figsize=(6, plotcount*3)
                             )

    #First plot the signal
    if plotcount > 1: 
        ax = axes[0]
    elif plotcount == 1: 
        ax = axes
        
    ax.plot(signal)
    ax.set_title('Signal')
    
    #Scale signal
    ax.set_ylim(signal.min()*.5, signal.max()*1.5)
    ax.set_xlim(0, len(signal))
        
    #Plot a horizontal line where the stop_point is indicated
    if stop_point is not None: 
        assert (stop_point > 0) & (stop_point < len(signal))
        ax.vlines(x=stop_point, ymin=0, ymax=ax.get_ylim()[1], 
                  colors='r', linestyles='dotted')
    
    #Now plot each residual
    if residuals is not None: 
        for ii, (res_name, res_values) in enumerate(residuals.iteritems()):
            ax = axes[ii+1]
            ax.plot(res_values)
            ax.set_title("Residual #{}: {}".format(ii+1, res_name))
            if scale: 
                ax.set_ylim(res_values.min()*0.5, res_values.max() * 1.5)
            ax.vlines(x=stop_point, ymin=0, ymax=ax.get_ylim()[1], 
                      colors='r', linestyles='dotted')
        


# ## Demo the results

# In[16]:

"""
Uncomment the following code to output the demo.
"""

'''
sig1 = np.ones(1000)
sig1[:500] = sig1[:500] * 50
sig1[500:] = sig1[500:] * 40

blank_detector = change_detector()
residuals = run_online_simulation(sig1, blank_detector)
'''


# Out[16]:

#     '\nsig1 = np.ones(1000)\nsig1[:500] = sig1[:500] * 50\nsig1[500:] = sig1[500:] * 40\n\nblank_detector = change_detector()\nresiduals = run_online_simulation(sig1, blank_detector)\n'

# (Note that the stopping rule will not be triggered, because we haven't created a stopping rule yet.)

# ### Convert to ipynb
# Convert this ipynb to python file so we can import it from other notebooks in the tutorial

# In[30]:

if __name__ == "__main__": 
    get_ipython().system(u'ipython nbconvert --to python scaffolding.ipynb')


# Out[30]:

#     [NbConvertApp] Using existing profile dir: u'/home/aman/.config/ipython/profile_default'
#     [NbConvertApp] WARNING | pattern u'../python_code/scaffolding.ipynb' matched no files
#     This application is used to convert notebook files (*.ipynb) to various other
#     formats.
#     
#     WARNING: THE COMMANDLINE INTERFACE MAY CHANGE IN FUTURE RELEASES.
#     
#     Options
#     -------
#     
#     Arguments that take values are actually convenience aliases to full
#     Configurables, whose aliases are listed on the help line. For more information
#     on full configurables, see '--help-all'.
#     
#     --debug
#         set log level to logging.DEBUG (maximize logging output)
#     --init
#         Initialize profile with default config files.  This is equivalent
#         to running `ipython profile create <profile>` prior to startup.
#     --quiet
#         set log level to logging.CRITICAL (minimize logging output)
#     --stdout
#         Write notebook output to stdout instead of files.
#     --profile=<Unicode> (BaseIPythonApplication.profile)
#         Default: u'default'
#         The IPython profile to use.
#     --ipython-dir=<Unicode> (BaseIPythonApplication.ipython_dir)
#         Default: u'/home/aman/.config/ipython'
#         The name of the IPython directory. This directory is used for logging
#         configuration (through profiles), history storage, etc. The default is
#         usually $HOME/.ipython. This options can also be specified through the
#         environment variable IPYTHONDIR.
#     --writer=<DottedObjectName> (NbConvertApp.writer_class)
#         Default: 'FilesWriter'
#         Writer class used to write the  results of the conversion
#     --log-level=<Enum> (Application.log_level)
#         Default: 30
#         Choices: (0, 10, 20, 30, 40, 50, 'DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL')
#         Set the log level by value or name.
#     --to=<CaselessStrEnum> (NbConvertApp.export_format)
#         Default: 'html'
#         Choices: ['custom', 'html', 'latex', 'markdown', 'python', 'rst', 'slides']
#         The export format to be used.
#     --template=<Unicode> (Exporter.template_file)
#         Default: u'default'
#         Name of the template file to use
#     --output=<Unicode> (NbConvertApp.output_base)
#         Default: ''
#         overwrite base name use for output files. can only  be use when converting
#         one notebook at a time.
#     --post=<DottedOrNone> (NbConvertApp.post_processor_class)
#         Default: u''
#         PostProcessor class used to write the  results of the conversion
#     --config=<Unicode> (BaseIPythonApplication.extra_config_file)
#         Default: u''
#         Path to an extra config file to load.
#         If specified, load this config file in addition to any other IPython config.
#     --profile-dir=<Unicode> (ProfileDir.location)
#         Default: u''
#         Set the profile location directly. This overrides the logic used by the
#         `profile` option.
#     
#     To see all available configurables, use `--help-all`
#     
#     Examples
#     --------
#     
#         The simplest way to use nbconvert is
#         
#         > ipython nbconvert mynotebook.ipynb
#         
#         which will convert mynotebook.ipynb to the default format (probably HTML).
#         
#         You can specify the export format with `--to`.
#         Options include ['custom', 'html', 'latex', 'markdown', 'python', 'rst', 'slides']
#         
#         > ipython nbconvert --to latex mynotebook.ipnynb
#         
#         Both HTML and LaTeX support multiple output templates. LaTeX includes
#         'basic', 'book', and 'article'.  HTML includes 'basic' and 'full'.  You 
#         can specify the flavor of the format used.
#         
#         > ipython nbconvert --to html --template basic mynotebook.ipynb
#         
#         You can also pipe the output to stdout, rather than a file
#         
#         > ipython nbconvert mynotebook.ipynb --stdout
#         
#         A post-processor can be used to compile a PDF
#         
#         > ipython nbconvert mynotebook.ipynb --to latex --post PDF
#         
#         You can get (and serve) a Reveal.js-powered slideshow
#         
#         > ipython nbconvert myslides.ipynb --to slides --post serve
#         
#         Multiple notebooks can be given at the command line in a couple of 
#         different ways:
#         
#         > ipython nbconvert notebook*.ipynb
#         > ipython nbconvert notebook1.ipynb notebook2.ipynb
#         
#         or you can specify the notebooks list in a config file, containing::
#         
#             c.NbConvertApp.notebooks = ["my_notebook.ipynb"]
#         
#         > ipython nbconvert --config mycfg.py
#     
# 

# In[ ]:



