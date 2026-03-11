public class Magicien extends Profil {
    public Magicien() {
        super("Magicien", 4);
    }

    @Override
    public int calculerPV(int modCon) {
        return 4 + modCon;
    }

    @Override
    public int getAttaqueMagique(int modInt, int modSag) {
        return modInt + 1;
    }
}
