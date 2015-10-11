#ifndef CARMA_HPP
#define CARMA_HPP

#include <complex>
#include <mkl_types.h>
#define MKL_Complex8 std::complex<float>
#define MKL_Complex16 std::complex<double>
#include <mkl.h>

using namespace std;

double calcCARMALnLike(const vector<double> &x, vector<double>& grad, void* p2Args);

double calcCARMALnLike(double* walkerPos, void* vdPtr2LnLikeArgs);

double calcLnLike(const vector<double> &x, vector<double>& grad, void* p2Args);

double calcLnLike(double* walkerPos, void* vdPtr2LnLikeArgs);

class CARMA {
private:
	int allocated;
	int isStable;
	int isInvertible;
	int isNotRedundant;
	int hasUniqueEigenValues;
	int p;
	int q;
	int pSq;
	int qSq;
	double t; // This is the last used step time to compute F and Q.
	// ilo, ihi and abnrm are arrays of size 1 so they can be re-used by everything. No need to make multiple copies for A, CAR and CMA
	lapack_int *ilo; // len 1
	lapack_int *ihi; // len 1
	double *abnrm; // len 1

	// Arrays used to compute expm(A dt)
	complex<double> *w; // len p
	complex<double> *expw; // len pSq
	complex<double> *CARMatrix; // len pSq
	complex<double> *CMAMatrix; // len qSq
	complex<double> *CARw; // len p
	complex<double> *CMAw; // len q
	double *scale; // len p
	complex<double> *vr; // len pSq
	complex<double> *vrInv; // len pSq
	double *rconde; // len p
	double *rcondv; // len p
	lapack_int *ipiv; // len p

	double *Theta; /*!< Theta contains p CAR parameters followed by q+1 CMA parameters, i.e. \f$\Theta = [a_{1}, a_{2}, ..., a_{p-1}, a_{p}, b_{0}, b_{1}, ..., b_{q-1}, b_{q}]\f$, where we follow the notation in Brockwell 2001, Handbook of Statistics, Vol 19.*/
	complex<double> *A;
	complex<double> *B;
	double *I;
	double *F;
	complex<double> *AScratch;
	complex<double> *BScratch;
	double *FKron;
	double *FKron_af;
	double *FKron_r;
	double *FKron_c;
	lapack_int *FKron_ipiv;
	double *FKron_rcond;
	double *FKron_rpvgrw;
	double *FKron_berr;
	double *FKron_err_bnds_norm;
	double *FKron_err_bnds_comp;
	double *D;
	double *Q;
	double *H;
	double *R;
	double *K;
	double *X;
	double *P;
	double *XMinus;
	double *PMinus;
	double *VScratch;
	double *MScratch;
public:
	CARMA();
	~CARMA();
	int get_p();
	int get_q();
	double get_t();
	void set_t(double t_incr);
	int get_allocated();
	void allocCARMA(int numP, int numQ);
	void deallocCARMA();
	int checkCARMAParams(double* ThetaIn); /*!< Function to check the validity of the CARMA parameters. Theta contains \f$p\f$ CAR parameters followed by \f$q+1\f$ CMA parameters, i.e. \f$\Theta = [a_{1}, a_{2}, ..., a_{p-1}, a_{p}, b_{0}, b_{1}, ..., b_{q-1}, b_{q}]\f$, where we follow the notation in Brockwell 2001, Handbook of Statistics, Vol 19.*/
	void setCARMA(double* ThetaIn); /*!< Function to set a CARMA object with the given CARMA parameters. Theta contains p CAR parameters followed by q+1 CMA parameters, i.e. \f$\Theta = [a_{1}, a_{2}, ..., a_{p-1}, a_{p}, b_{0}, b_{1}, ..., b_{q-1}, b_{q}]\f$, where we follow the notation in Brockwell 2001, Handbook of Statistics, Vol 19.*/
	void operator()(const vector<double> &x, vector<double> &dxdt, const double xi);
	void solveCARMA();
	void resetState(double InitUncertainty);
	void resetState();
	void getCARRoots(complex<double>*& CARoots);
	void getCMARoots(complex<double>*& CMARoots);
	void burnSystem(int numBurn, unsigned int burnSeed, double* burnRand);
	double observeSystem(double distRand, double noiseRand);
	double observeSystem(double distRand, double noiseRand, double mask);
	void observeSystem(int numObs, unsigned int distSeed, unsigned int noiseSeed, double* distRand, double* noiseRand, double noiseSigma, double* y);
	void observeSystem(int numObs, unsigned int distSeed, unsigned int noiseSeed, double* distRand, double* noiseRand, double noiseSigma, double* y, double* mask);
	double computeLnLike(int numPts, double* y, double* yerr);
	double computeLnLike(int numPts, double* y, double* yerr, double* mask);
	void getResiduals(int numPts, double* y, double* r);
	void fixedIntervalSmoother(int numPts, double* y, double* r, double* x);
	};

struct LnLikeData {
	int numPts;
	double* y;
	double* yerr;
	double* mask;
	};

struct LnLikeArgs {
	int numThreads;
	CARMA* Systems;
	LnLikeData Data;
	}; 

void zeroMatrix(int nRows, int nCols, int* mat);

void zeroMatrix(int nRows, int nCols, double* mat);

void zeroMatrix(int nRows, int nCols, complex<double>* mat);

void viewMatrix(int nRows, int nCols, int* mat);

void viewMatrix(int nRows, int nCols, double* mat);

void viewMatrix(int nRows, int nCols, complex<double>* mat);

double dtime();

void kron(int m, int n, double* A, int p, int q, double* B, double* C);

void expm(double xi, double* out);

#endif
