#include "colorfilter.h"

int index(int colormap[][4], int cmaplength, int color[4]) {
	for (int i=0; i<cmaplength; i++) {
		if ((colormap[i][0]==color[0]) && 
			(colormap[i][1]==color[1]) &&
			(colormap[i][2]==color[2]) &&
			(colormap[i][3]==color[3]) ) {
			return i;
		}
	}
	int closest;
	int dist, distance = INT_MAX;
	for (int i=0; i<cmaplength; i++) {
		if (color[3] != 0){
			dist = ((colormap[i][0]-color[0])*(colormap[i][0]-color[0])+
					(colormap[i][1]-color[1])*(colormap[i][1]-color[1])+
					(colormap[i][2]-color[2])*(colormap[i][2]-color[2])+
					3*(colormap[i][3]-color[3])*(colormap[i][3]-color[3]));
		} else {
			dist = (colormap[i][3]-color[3])*(colormap[i][3]-color[3]);
		}
		if (dist < distance) {
			closest = i;
			distance = dist;
		}
	}
	return closest;
}

int* indexiterate(int colormap[][4], int cmaplength, int colors[][4], int length) { 
	int * results = new int[length];
	int color[4];
	for (int i=0; i<length; i++) {
		for (int j=0; j<4; j++) {
			color[j] = colors[i][j];
		}
		results[i] = index(colormap, cmaplength, color);
	}
	return results;
}

int* colormap(int colors[][4], int length, int size){

}