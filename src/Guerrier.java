public class Guerrier extends Profil {
    public Guerrier() {
        super("Guerrier", 10);
    }

    @Override
    public int calculerPV(int modCon) {
        return 10 + modCon;
    }

    @Override
    public int getAttaqueMagique(int modInt, int modSag) {
        return 0;
    }
}
