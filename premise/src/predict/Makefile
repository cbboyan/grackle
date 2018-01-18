CXXFLAGS = -static -std=c++11 -O2 -Wall -g

all: predict

predict: main.cpp predictor.cpp format.cpp knn.cpp mepo.cpp nbayes.cpp rforest.cpp tfidf.cpp dtree.cpp
	g++ $(CXXFLAGS) $(MODE) $< -o $@

clean:
	rm predict
