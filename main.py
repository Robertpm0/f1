from itertools import count
import fastf1.plotting
from fastf1.ergast import Ergast
import streamlit as st
import fastf1
import streamlit.components.v1 as components
from matplotlib.animation import FuncAnimation
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#fastf1.Cache.clear_cache()
ergast=Ergast()
def getRace(szn):
    races=ergast.get_circuits(szn)
    #print(races)
    return races.circuitId



fastf1.plotting.setup_mpl(misc_mpl_mods=False)


szns= ergast.get_seasons(limit=99)

st.title("F1 Race Analyzer")

# plots position changes and track turns for a give race and season
def showDat(year, race):
    # grabbing race data from fastf1
    session = fastf1.get_session(year, race, 'R')
    session.load()
    ##time.sleep(5)
    try:
        numLaps=session.laps.nunique()[4] # total laps in race
    except:
        st.error("Error Fetching Race data from fastf1 API")
    lap = session.laps.pick_fastest() 
    pos = lap.get_pos_data()
    trackData=session.get_circuit_info()

    #print(num)
    colors = []
    drivers = []
    laps = []
    positions = []
    teams=[]
    dnfs=0
    #xy=0
    count2=1
    #print("DRIVERS",session.drivers)
    for drv in session.drivers: # looping all drivers and getting their position data
        
        drv_laps = session.laps.pick_driver(drv)
        abb = drv_laps['Driver'].iloc[0] # driver abbreviation eg "HAM" for LH44
        team=drv_laps["Team"].iloc[0]
        # trying to get official driver color if exists else just get team color
        # because some drivrs dont have colors like backups/new replacements
        try:
            col = fastf1.plotting.driver_color(abb)
        except:
            col=fastf1.plotting.team_color(team)

        colors.append([col]*numLaps)

        drivers.append([abb]*numLaps)
        teams.append([team]*numLaps)
        
        if len(drv_laps["LapNumber"])<numLaps:
            # making number of laps = length for plotting purposes on drivers who dnf
            newData=np.array(drv_laps["LapNumber"])
            dif=numLaps-len(newData)
            newData=np.append(newData,[len(newData)]*dif)
            laps.append(newData)
        else:
            laps.append(drv_laps['LapNumber'])

        if len(drv_laps["Position"])<numLaps:
            # having to add drivers dnf position to remaining laps for plotting purposes

            newData2=np.array(drv_laps["Position"])
            dif=numLaps-len(newData2)
            dnfPlace=count2
            newData2=np.append(newData2,[dnfPlace]*dif)
            positions.append(newData2)
            dnfs=dnfs+1
        else:
            dl=drv_laps["Position"].copy()
            dl.iloc[-1]=count2

            positions.append(dl)

        count2=count2+1

    drivers=np.array(drivers).flatten()
    colors=np.array(colors).flatten()
    laps=np.array(laps).flatten()
    positions=np.array(positions).flatten()
    teams=np.array(teams).flatten()


    # plotting results #
    d={
            'Drivers':drivers,
            'Colors':colors,
            'Laps':laps,
            'Positions':positions
    }
    dd=pd.DataFrame(d)
    numDrivers=dd.Drivers.unique()
    fig, axes = plt.subplots(figsize=(8.0, 4.9))
    #axes.legend(labels=dd.Drivers.unique())
    axes.set_xlim([0,numLaps]) 
    axes.set_ylim([20.5, 0.5])
    axes.set_yticks([1, 5, 10, 15, 20])

    axes.set_xlabel('Lap')
    axes.set_ylabel('Position')


    x1,y1=[],[[] for _ in range(len(numDrivers))]
    myVar=count(0,1)

    # animating pos changes
    def ani(i):
        fig.tight_layout()

        x1.append(next(myVar))
        j=i

        raceFigs=[]
        for d in range(0,len(numDrivers)):
            driverData=dd[dd.Drivers==numDrivers[d]].iloc[i]
            y1[d].append(driverData.Positions)

        for d in range(0,len(numDrivers)):
            #plotting each fig as a frame by frame animation
            raceFig, =axes.plot(x1,y1[d],color=dd[dd.Drivers==numDrivers[d]].iloc[0]["Colors"],
                      label=dd[dd.Drivers==numDrivers[d]].iloc[0]["Drivers"],marker=r"$ {} $".format(numDrivers[d]),markevery=10000)
            raceFigs.append(raceFig)
        if j==numLaps-1:
            # plotting legend if last lap legend based on final pos
            axes.legend(raceFigs,[x.get_label() for x in raceFigs],bbox_to_anchor=(1.0,1.02)).set_in_layout(True)
            fig.tight_layout()

            
    #axes.legend()
    st.subheader(str(race)+" Race Results")
    anim=FuncAnimation(fig,ani,frames=numLaps,interval=90,blit=False)
    # plotting top 3
    lastLap=dd[dd.Laps==numLaps][["Drivers","Positions"]]
    winner=lastLap[lastLap.Positions==1].Drivers.values
    sec=lastLap[lastLap.Positions==2].Drivers.values
    thr=lastLap[lastLap.Positions==3].Drivers.values

    st.subheader("🥇 P1: "+ winner)
    st.subheader("🥈P2: "+ sec)
    st.subheader("🥉P3: "+ thr)
    #st.subheader("DNFs: "+str(dnfs))
    #print(dnfs)
    t1,t2=st.tabs(["Positions","Turns"])
    st.toast("Generating Chart Media")
    
    with t1:
        # streamlit trick to plot animation
        components.html(anim.to_jshtml(),width=1200,height=1000)
    with t2:
        #plotting turns and race map, code mostly from fastf1 docs
        plt.style.use("bmh")
        fig2, ax2 = plt.subplots(figsize=(10.0, 6.9))
        track = pos.loc[:, ('X', 'Y')].to_numpy()
        track_angle = trackData.rotation / 180 * np.pi
        def rotate(xy, *, angle):
            rot_mat = np.array([[np.cos(angle), np.sin(angle)],
                            [-np.sin(angle), np.cos(angle)]])
            return np.matmul(xy, rot_mat)

    # Rotate and plot the track map.
        rotated_track = rotate(track, angle=track_angle)
        trackPlot=ax2.plot(rotated_track[:, 0], rotated_track[:, 1])
        offset_vector = [500, 0]  # offset length is chosen arbitrarily to 'look good'

        # Iterate over all corners.
        for _, corner in trackData.corners.iterrows():
            #print(corner["Angle"])
            if abs(corner["Angle"]) <40:
                continue
        # Create a string from corner number and letter
            txt = f"{corner['Number']}{corner['Letter']}"

        # Convert the angle from degrees to radian.
            offset_angle = corner['Angle'] / 180 * np.pi

        # Rotate the offset vector so that it points sideways from the track.
            offset_x, offset_y = rotate(offset_vector, angle=offset_angle)

        # Add the offset to the position of the corner
            text_x = corner['X'] + offset_x
            text_y = corner['Y'] + offset_y

        # Rotate the text position equivalently to the rest of the track map
            text_x, text_y = rotate([text_x, text_y], angle=track_angle)

        # Rotate the center of the corner equivalently to the rest of the track map
            track_x, track_y = rotate([corner['X'], corner['Y']], angle=track_angle)

        # Draw a circle next to the track.
            ax2.scatter(text_x, text_y, color='grey', s=140)

        # Draw a line from the track to this circle.
            ax2.plot([track_x, text_x], [track_y, text_y], color='grey')

        # Finally, print the corner number inside the circle.
            ax2.text(text_x, text_y, txt,
                va='center_baseline', ha='center', size='small', color='white')
        plt.title(str(race)+"Circuit Turns")
        plt.xticks([])
        plt.yticks([])
        plt.axis('equal')
        st.write(fig2)
    st.text("Number of Turns:")
    st.text(txt)

# streamlit user inputs
st.sidebar.header("Select a Season")
xx=st.sidebar.selectbox("Seasons",options=szns.season)
st.sidebar.header("Select a Race")
yy=st.sidebar.selectbox("Races",options=getRace(xx))

if st.sidebar.button("Plot!"):
    st.toast("Grabbing race result data")
    showDat(xx, yy)
