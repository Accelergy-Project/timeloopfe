install_timeloop:
	git clone https://github.com/Accelergy-Project/timeloop-pim-update.git timeloop
	cp update_timeloop_inputs.py timeloop/
	cd timeloop && echo "YES" | python3 update_timeloop_inputs.py
	# sudo apt install scons libconfig++-dev libboost-dev libboost-iostreams-dev libboost-serialization-dev libyaml-cpp-dev libncurses-dev libtinfo-dev libgpm-dev git build-essential python3-pip
	cd timeloop && cp -r pat-public/src/pat src/pat
	cd timeloop && scons --accelergy --static -j 16
	cd timeloop && cp build/timeloop* ~/.local/bin

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
