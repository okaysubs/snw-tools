#include <climits>
using namespace std;

extern "C" __declspec(dllexport) int* indexiterate(int colormap[][4], int cmaplength, int color[][4], int length);
extern "C" __declspec(dllexport) int index(int colormap[][4], int cmaplength, int color[4]);