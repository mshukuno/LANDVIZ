LANDVIZ (LANDIS-II-Visualization)
========================

Changes to this extension are governed by the [**Repository Rules**](https://sites.google.com/site/landismodel/developers/developers-blog/repositoryrulesfromthetechnicaladvisorycommittee) from the Technical Advisory Committee.

LANDIS-II Visualization Development

Documentaion: Documentation of the PreProcTool and the WebVisTool

PreProcTool: Development environment for the PrePrcoTool

WebWisTool: Development environment for the WebVisTool

<br></br>
<br></br>
## LANDVIZ v2.0
#### Edit extension metadata (_optional_)

##### merge & update
_When to use?_ </br>
Multiple extension metadata need to be modified for the LANDVIZ tool.
###### merge
The tool merges the LANDIS-II Extensions' metadata into one XML file. It makes easy
to edit multiple extensions' metadata on one file.</br>
```preproctool-v2 merge -p {project XML file path} -f {output XML file name}```
###### update
The tool updates metadata according to changes made on
the merged XML file.</br>
```preproctool-v2 update -p {project XML file path} -f {merged XML file name}```  
##### timesteps
The tool adds skipped time steps for CSV log file. Currently, only two types 
of CSV log files are supported - Base BDA and a simple CSV extension log file
having all numeric attributes.

| Flags | Descriptions |
| -----| ----------- |
| -i    | CSV file path |
| -f    | Output CSV file path |
| -ts_c | Time step column name |
| -ts_i | Time step interval |
| -ts_min | Minimum time step |
| -ts_max | Maximum time step |
| -g    | Group by column name |

Base BDA:</br>
Group by "AgentName" and adds skipped time steps and add rest of attributes
to be 0s.

```
preproctool-v2 timesteps 
-i "path to\bda-log.csv" 
-f "bda-log.csv"
-ts_c "Time"
-ts_i 1
-ts_min 0
-ts_max 114
-g "AgentName"
```
Simple CSV log (all attributes are numeric)
Use without ```-g``` flag.
</br>
</br>

#### Updates
* Updated to Python 3.7 from Python 2.7
* Enabled the LandViz pre-processing tool (PreProcTool) to handle cases when maps are missing or are present but empty (these currently cause PreProcTool to crash).
    * If data is empty (all 0’s or none) - not creating map tiles.
    * If data does not exist - not creating map tiles.
* Added ```merge``` and ```update``` tools for metadata edit.
* Added log for missing map time steps.
* Added ```timesteps``` tool to add missing time steps for Base BDA, and 
  a simple CSV extension log file having all numeric attributes.
* Updated the tool logging
    * Includes log for the tilerstool.
* Updated jQuery library from 2.x to 3.5 in LANDVIZ Web.
* Changed the tool name to PreProcTool-v2 from PreProcTool.

#### Uninstall
The installer install application in ```C:\Program Files\LANDIS-II-v7\LANDVIZ-v2``` and adds system Path environment variable.
To uninstall, double click ```unins000.exe```. It will remove the application and environment variable.  The files and 
folders created after the installation such as logs folder and log files will not be removed by uninstaller.

## LANDVIZ v1.2

#### Updates 
* Added "Load" button (#22).
* Added "modal" to onload (#23) - Information showing on the modal is old.  It still needs to be updated.
* Added "Information" button for external web liks.  The user can add web links in XML (#24).
* Adjusted colors on graphs (#25).
* "Reset" button added (#26).

#### Notes
* (#24) text and video needs to be reviewed and modified.
* Documentations need to be updated.

#### Testing
1. Download or clone the project and unzip.
2. Go to **_example/example\_project_** folder and open **_preproc\_VizTool\_example.xml_** file. The tag ```<weblinks></weblinks>``` is a new to this release.  Modify ```<link>``` applicable to your project.  The order of tags is important so use **_preproc\_VizTool\_example.xml_** as a template.
```xml
<weblinks>
	<link label="LandViz" href="https://sites.google.com/site/landismodel/tools/viz-tool" />
	<link label="Dynamic Ecosystems &amp; Landscape Lab" href="https://sites.google.com/a/ncsu.edu/dynamic-ecosystems-landscape-lab" />
</weblinks>
```
The ```<weblinks>``` tag requires at least one ```<link>``` child node in order to run the application successfully. 
```xml
<weblinks>
	<link label="LandViz" href="https://sites.google.com/site/landismodel/tools/viz-tool" />
</weblinks>
```
3. Dobule click **_example/example\_project/run\_preproctool\_example.bat_** file.  The **"sample\_output"** file will be created after the successful run.
4. Double click **_sample_output/start-landis-vis-local.exe_**.  It will open **LANDVIZ-II-Visualization** webpage.



