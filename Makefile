install_timeloop:
	rm -rf build
	mkdir build
	cp -r timeloop build/
	# One-time installs
	# cd build && git clone https://github.com/NVlabs/timeloop.git
	# export BARVINOK_VER=0.41.6
	# export NTL_VER=11.5.1
	# cd build
	# wget https://libntl.org/ntl-$NTL_VER.tar.gz \
	# 	   && tar -xvzf ntl-$NTL_VER.tar.gz \
	# 	   && cd ntl-$NTL_VER/src \
	# 	   && ./configure NTL_GMP_LIP=on SHARED=on \
	# 	   && make \
	# 	   && make install
    # wget https://barvinok.sourceforge.io/barvinok-$BARVINOK_VER.tar.gz \
	#      && tar -xvzf barvinok-$BARVINOK_VER.tar.gz \
	#      && cd barvinok-$BARVINOK_VER \
	#      && ./configure --enable-shared-barvinok \
	#      && make \
    #      && make install
	# sudo apt install scons libconfig++-dev libboost-all-dev libboost-dev libboost-iostreams-dev libboost-serialization-dev libyaml-cpp-dev libncurses-dev libtinfo-dev libgpm-dev git build-essential python3-pip
	cp update_timeloop_inputs.py build/timeloop/
	cd build/timeloop && echo "YES" | python3 update_timeloop_inputs.py
	cd build/timeloop && cp -r pat-public/src/pat src/pat
	cd build/timeloop && cp -r pat-public/src/pat include/pat
	cd build/timeloop && scons --accelergy --static --with-isl -j 24
	cd build/timeloop && cp build/timeloop* ~/.local/bin

install_infrastructure:
	git clone --recurse-submodules https://github.com/Accelergy-Project/accelergy-timeloop-infrastructure.git
	cd accelergy-timeloop-infrastructure/src/cacti ; make
	cd accelergy-timeloop-infrastructure/src/accelergy-neurosim-plug-in ; make
	pip3 install accelergy-timeloop-infrastructure/src/accelergy
	pip3 install accelergy-timeloop-infrastructure/src/accelergy-aladdin-plug-in
	pip3 install accelergy-timeloop-infrastructure/src/accelergy-cacti-plug-in
	pip3 install accelergy-timeloop-infrastructure/src/accelergy-table-based-plug-ins
	pip3 install accelergy-timeloop-infrastructure/src/accelergy-neurosim-plug-in
	pip3 install accelergy-timeloop-infrastructure/src/accelergy-library-plug-in
	pip3 install accelergy-timeloop-infrastructure/src/accelergy-adc-plug-in
	cp -r accelergy-timeloop-infrastructure/src/cacti \
	   ~/.local/share/accelergy/estimation_plug_ins/accelergy-cacti-plug-in/

install:
	make install_timeloop
	make install_infrastructure
	pip3 install .
	make clean

clean:
	rm -rf timeloop
	rm -rf accelergy-timeloop-infrastructure
	rm -rf build
